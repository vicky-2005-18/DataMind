"""Experiment service: orchestrates modeling, splitting, training, finalization, and persistence."""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from typing import List, Optional

import joblib

from datamind.config import get_settings
from datamind.contracts import (
    AlgorithmConfig,
    ErrorCode,
    ExperimentSummary,
    HoldoutEvaluation,
    ModelingView,
    PreprocessingConfig,
    RowPolicy,
    ServiceError,
    SplitManifest,
    TaskType,
)
from datamind.ml.experiment import run_experiment, score_holdout
from datamind.ml.modeling import build_modeling_view
from datamind.ml.splitting import create_split_manifest
from datamind.services.datasets import DatasetService
from datamind.storage.experiment_repos import (
    EvaluationRepository,
    ExperimentRepository,
    SplitRepository,
)
from datamind.storage.locks import WorkspaceLock


class ExperimentService:
    """
    Service that orchestrates the full supervised ML workflow,
    including cross-validation, champion persistence, holdout finalization, and config cloning.
    """

    def __init__(
        self,
        dataset_service: Optional[DatasetService] = None,
        split_repo: Optional[SplitRepository] = None,
        experiment_repo: Optional[ExperimentRepository] = None,
        eval_repo: Optional[EvaluationRepository] = None,
        lock: Optional[WorkspaceLock] = None,
    ):
        settings = get_settings()
        self.dataset_service = dataset_service or DatasetService()
        self.split_repo = split_repo or SplitRepository(settings.db_path)
        self.experiment_repo = experiment_repo or ExperimentRepository(settings.db_path)
        self.eval_repo = eval_repo or EvaluationRepository(settings.db_path)
        lock_file = settings.locks_dir / "workspace.lock"
        self.lock = lock or WorkspaceLock(lock_file)

    def prepare_modeling_view(
        self,
        dataset_id: str,
        task: TaskType,
        target: str,
        numeric_features: List[str],
        categorical_features: List[str],
        row_policy: Optional[RowPolicy] = None,
    ) -> ModelingView:
        """Validate modeling configuration and build an immutable ModelingView."""
        dataset = self.dataset_service.get_dataset(dataset_id)
        if dataset is None:
            raise ServiceError(
                ErrorCode.DATASET_NOT_FOUND,
                f"Dataset '{dataset_id}' not found.",
                field="dataset_id",
            )
        df = self.dataset_service.load_dataframe(dataset_id)
        return build_modeling_view(
            dataset=dataset,
            df=df,
            task=task,
            target=target,
            numeric_features=numeric_features,
            categorical_features=categorical_features,
            row_policy=row_policy,
        )

    def prepare_split(
        self,
        dataset_id: str,
        view: ModelingView,
        test_fraction: float = 0.20,
        cv_folds: int = 5,
        random_seed: int = 42,
    ) -> SplitManifest:
        """Create (or retrieve cached) split manifest for a ModelingView."""
        df = self.dataset_service.load_dataframe(dataset_id)
        y = df[view.target]
        manifest = create_split_manifest(
            view=view,
            y=y,
            test_fraction=test_fraction,
            cv_folds=cv_folds,
            random_seed=random_seed,
        )
        # Persist (INSERT OR IGNORE handles deduplication by fingerprint)
        self.split_repo.create(manifest, view.row_policy)
        return manifest

    def run_supervised_experiment(
        self,
        experiment_name: str,
        project_id: str,
        dataset_id: str,
        view: ModelingView,
        manifest: SplitManifest,
        algorithm_configs: List[AlgorithmConfig],
        prep_config: Optional[PreprocessingConfig] = None,
        seed: int = 42,
        submission_token: Optional[str] = None,
    ) -> ExperimentSummary:
        """
        Execute CV training for all algorithms and persist results under WorkspaceLock.
        Enforces cross-project ownership and submission token idempotency.
        Holdout is NOT scored here.
        """
        # T41: Cross-project reference validation
        dataset = self.dataset_service.get_dataset(dataset_id)
        if dataset is None or dataset.project_id != project_id:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                f"Dataset '{dataset_id}' does not belong to project '{project_id}'.",
                field="dataset_id",
            )
        if manifest.dataset_id != dataset_id:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                f"Split '{manifest.split_id}' does not belong to dataset '{dataset_id}'.",
                field="split_id",
            )

        # Compute submission token if not provided
        if not submission_token:
            config_payload = {
                "experiment_name": experiment_name,
                "project_id": project_id,
                "dataset_id": dataset_id,
                "view_fingerprint": view.view_fingerprint,
                "split_fingerprint": manifest.split_fingerprint,
                "algorithm_configs": [a.model_dump() for a in algorithm_configs],
                "prep_config": (prep_config or PreprocessingConfig()).model_dump(),
                "seed": seed,
            }
            submission_token = hashlib.sha256(json.dumps(config_payload, sort_keys=True).encode()).hexdigest()

        # T22: Submit token idempotency check
        existing = self.experiment_repo.get_by_submission_token(submission_token)
        if existing is not None:
            return existing

        # T22: Concurrency lock
        with self.lock.acquire():
            # Re-check idempotency under lock in case of race
            existing = self.experiment_repo.get_by_submission_token(submission_token)
            if existing is not None:
                return existing

            df = self.dataset_service.load_dataframe(dataset_id)
            summary = run_experiment(
                experiment_name=experiment_name,
                project_id=project_id,
                dataset_id=dataset_id,
                df=df,
                view=view,
                manifest=manifest,
                algorithm_configs=algorithm_configs,
                prep_config=prep_config,
                seed=seed,
            )
            # Ensure submission token matches
            summary.submission_token = submission_token
            self.experiment_repo.save_experiment(summary)
            return summary

    def finalize_experiment(self, experiment_id: str) -> HoldoutEvaluation:
        """
        Idempotently evaluate champion on sequestered holdout rows.
        Records holdout_previously_exposed if this split was evaluated previously.
        """
        # T22: Concurrency lock
        with self.lock.acquire():
            # T25: Idempotent finalization — if already finalized, return existing record
            existing_eval = self.eval_repo.get_evaluation(experiment_id)
            if existing_eval is not None:
                return existing_eval

            experiment = self.get_experiment(experiment_id)
            if experiment is None:
                raise ServiceError(
                    ErrorCode.INVALID_MODEL_CONFIG,
                    f"Experiment '{experiment_id}' not found.",
                    field="experiment_id",
                )

            if not experiment.selected_trial_id:
                raise ServiceError(
                    ErrorCode.TRAINING_FAILED,
                    f"Experiment '{experiment_id}' has no champion trial to finalize.",
                    field="selected_trial_id",
                )

            if not experiment.split_id:
                raise ServiceError(
                    ErrorCode.INVALID_MODEL_CONFIG,
                    f"Experiment '{experiment_id}' has no associated split.",
                    field="split_id",
                )

            # T26: Check if split was previously exposed in any prior evaluation
            prior_exposed = self.eval_repo.is_split_holdout_exposed(experiment.split_id)

            # Load split manifest
            manifest = self.split_repo.get_by_id(experiment.split_id)
            if manifest is None:
                raise ServiceError(
                    ErrorCode.INVALID_MODEL_CONFIG,
                    f"Split manifest for split '{experiment.split_id}' could not be loaded.",
                )

            # Load saved champion pipeline artifact
            settings = get_settings()
            exp_dir = settings.experiments_dir / experiment_id
            model_path = exp_dir / "champion.joblib"
            if not model_path.exists():
                # Check trial specific name fallback
                model_path = exp_dir / f"{experiment.selected_trial_id}_champion.joblib"

            if not model_path.exists() or model_path.stat().st_size == 0:
                raise ServiceError(
                    ErrorCode.MODEL_UNAVAILABLE,
                    f"Trained champion model artifact for experiment '{experiment_id}' is unavailable or missing.",
                    field="model_artifact",
                )

            try:
                champion_pipeline = joblib.load(model_path)
            except Exception as exc:
                raise ServiceError(
                    ErrorCode.MODEL_UNAVAILABLE,
                    f"Trained champion model artifact for experiment '{experiment_id}' is corrupted: {exc}",
                    field="model_artifact",
                ) from exc

            # Load input schema
            schema_file = exp_dir / "input_schema.json"
            if not schema_file.exists():
                raise ServiceError(
                    ErrorCode.MODEL_UNAVAILABLE,
                    f"Input schema for experiment '{experiment_id}' is missing.",
                )
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_data = json.load(f)

            # Reconstruct minimal modeling view for scoring
            view = ModelingView(
                dataset_id=experiment.dataset_id,
                task=experiment.task,
                target=schema_data["target"],
                feature_names=schema_data["feature_names"],
                numeric_features=schema_data["numeric_features"],
                categorical_features=schema_data["categorical_features"],
                row_policy=RowPolicy(),
                eligible_row_ids=manifest.train_row_ids + manifest.test_row_ids,
                view_fingerprint=manifest.view_fingerprint,
            )

            # Load raw dataframe and slice holdout rows
            df = self.dataset_service.load_dataframe(experiment.dataset_id)
            holdout_df = df.loc[manifest.test_row_ids]

            # Score holdout data
            metrics, confusion_mat, class_labels = score_holdout(
                champion_pipeline=champion_pipeline,
                holdout_df=holdout_df,
                view=view,
                trial_id=experiment.selected_trial_id,
            )

            eval_id = str(uuid.uuid4())
            evaluation = HoldoutEvaluation(
                id=eval_id,
                experiment_id=experiment_id,
                trial_id=experiment.selected_trial_id,
                split_id=experiment.split_id,
                scope="holdout",
                holdout_previously_exposed=prior_exposed,
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                metrics=metrics,
                confusion_matrix=confusion_mat,
                class_labels=class_labels,
            )

            self.eval_repo.save_evaluation(evaluation)
            return evaluation

    def get_evaluation(self, experiment_id: str) -> Optional[HoldoutEvaluation]:
        """Retrieve the holdout evaluation for an experiment if finalized."""
        return self.eval_repo.get_evaluation(experiment_id)

    def clone_config(self, experiment_id: str) -> dict:
        """
        Clone an experiment's configuration into a draft dictionary for modification.
        Does NOT train immediately.
        """
        experiment = self.get_experiment(experiment_id)
        if experiment is None:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                f"Experiment '{experiment_id}' not found for cloning.",
            )
        try:
            config = json.loads(experiment.config_json)
        except Exception:
            config = {}

        return {
            "source_experiment_id": experiment.id,
            "experiment_name": f"Clone of {experiment.name}",
            "dataset_id": experiment.dataset_id,
            "task": experiment.task.value,
            "random_seed": experiment.random_seed,
            "config": config,
        }

    def list_experiments(self, project_id: str) -> List[ExperimentSummary]:
        """List all experiments for a project."""
        return self.experiment_repo.list_by_project(project_id)

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentSummary]:
        """Retrieve a full experiment with trials and metrics."""
        return self.experiment_repo.get_by_id(experiment_id)
