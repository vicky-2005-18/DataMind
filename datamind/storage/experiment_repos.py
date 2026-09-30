"""SQLite repository implementations for experiments, splits, and evaluations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from datamind.config import get_settings
from datamind.contracts import (
    ExperimentSummary,
    FoldIndices,
    HoldoutEvaluation,
    MetricDirection,
    MetricRecord,
    MetricScope,
    RowPolicy,
    SplitManifest,
    TaskType,
    TrialResult,
)
from datamind.storage.database import get_connection


class SplitRepository:
    """Repository for split manifest persistence."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def create(self, manifest: SplitManifest, row_policy: RowPolicy) -> str:
        """
        Create or return existing split record.
        Deduplicates on split_fingerprint and returns the persisted split id.
        """
        conn = get_connection(self.db_path)
        try:
            # Check for existing split with same fingerprint
            existing = conn.execute(
                "SELECT id FROM splits WHERE split_fingerprint = ?;",
                (manifest.split_fingerprint,),
            ).fetchone()
            if existing:
                return existing["id"]

            # Create new split
            split_id = manifest.split_id
            created_at = datetime.now(timezone.utc).isoformat()

            conn.execute(
                """
                INSERT INTO splits (
                    id, dataset_id, task, target, view_fingerprint, split_fingerprint,
                    config_json, row_policy_json, manifest_relative_path, manifest_sha256, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    split_id,
                    manifest.dataset_id,
                    manifest.task.value,
                    manifest.target,
                    manifest.view_fingerprint,
                    manifest.split_fingerprint,
                    json.dumps(
                        {
                            "test_fraction": manifest.test_fraction,
                            "cv_folds": manifest.cv_folds,
                            "random_seed": manifest.random_seed,
                        },
                        sort_keys=True,
                    ),
                    row_policy.model_dump_json(),
                    manifest.manifest_relative_path,
                    "",  # manifest_sha256 - will be computed by caller
                    created_at,
                ),
            )
            conn.commit()
            return split_id
        finally:
            conn.close()

    def get_by_id(self, split_id: str) -> Optional[SplitManifest]:
        """Get a split manifest by ID."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT id, dataset_id, task, target, view_fingerprint, split_fingerprint,
                       config_json, row_policy_json, manifest_relative_path, manifest_sha256, created_at
                FROM splits WHERE id = ?;
                """,
                (split_id,),
            ).fetchone()
            if row:
                config = json.loads(row["config_json"])
                row_policy = RowPolicy.model_validate_json(row["row_policy_json"])

                # Load and parse manifest JSON
                # Resolve relative path from storage directory
                settings = get_settings()
                manifest_file = settings.storage_dir / row["manifest_relative_path"]
                if manifest_file.exists():
                    manifest_data = json.loads(manifest_file.read_text())
                    folds = [
                        FoldIndices(
                            fold_index=f["fold_index"],
                            train_row_ids=f["train_row_ids"],
                            val_row_ids=f["val_row_ids"],
                        )
                        for f in manifest_data.get("folds", [])
                    ]
                    train_row_ids = manifest_data.get("train_row_ids", [])
                    test_row_ids = manifest_data.get("test_row_ids", [])
                else:
                    folds = []
                    train_row_ids = []
                    test_row_ids = []

                return SplitManifest(
                    split_id=row["id"],
                    dataset_id=row["dataset_id"],
                    view_fingerprint=row["view_fingerprint"],
                    split_fingerprint=row["split_fingerprint"],
                    task=TaskType(row["task"]),
                    target=row["target"],
                    test_fraction=config.get("test_fraction", 0.2),
                    cv_folds=config.get("cv_folds", 5),
                    random_seed=config.get("random_seed", 42),
                    train_row_ids=train_row_ids,
                    test_row_ids=test_row_ids,
                    folds=folds,
                    manifest_relative_path=row["manifest_relative_path"],
                )
            return None
        finally:
            conn.close()


class ExperimentRepository:
    """Repository for experiment persistence operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def save_experiment(self, summary: ExperimentSummary) -> None:
        """Save or update an experiment with its trials and metrics."""
        conn = get_connection(self.db_path)
        try:
            with conn:
                # Upsert experiment
                conn.execute(
                    """
                    INSERT INTO experiments (
                        id, project_id, dataset_id, split_id, task, name, status,
                        submission_token, config_json, config_sha256, comparison_key,
                        environment_json, registry_version, metric_version, random_seed,
                        primary_metric, retry_of_id, started_at, finished_at, error_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status = excluded.status,
                        finished_at = excluded.finished_at,
                        error_json = excluded.error_json;
                    """,
                    (
                        summary.id,
                        summary.project_id,
                        summary.dataset_id,
                        summary.split_id,
                        summary.task.value,
                        summary.name,
                        summary.status,
                        summary.submission_token,
                        summary.config_json,
                        "",  # config_sha256 - computed by caller
                        summary.comparison_key,
                        "",  # environment_json - populated by caller
                        "",  # registry_version
                        "",  # metric_version
                        summary.random_seed,
                        summary.primary_metric,
                        None,  # retry_of_id
                        summary.started_at,
                        summary.finished_at,
                        None,  # error_json - ExperimentSummary doesn't have error field
                    ),
                )

                # Save trials
                for trial in summary.trials:
                    conn.execute(
                        """
                        INSERT INTO trials (
                            id, experiment_id, algorithm_id, is_baseline, parameters_json,
                            status, fit_duration_seconds, warnings_json, error_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(experiment_id, algorithm_id) DO UPDATE SET
                            status = excluded.status,
                            fit_duration_seconds = excluded.fit_duration_seconds,
                            warnings_json = excluded.warnings_json,
                            error_json = excluded.error_json;
                        """,
                        (
                            trial.trial_id,
                            summary.id,
                            trial.algorithm_id,
                            1 if trial.is_baseline else 0,
                            json.dumps(trial.parameters, sort_keys=True),
                            trial.status,
                            trial.fit_duration_seconds,
                            json.dumps(trial.warnings, sort_keys=True),
                            json.dumps({"error": trial.error}) if trial.error else None,
                            summary.started_at,
                        ),
                    )

                    # Save metrics
                    for metric in trial.metrics:
                        conn.execute(
                            """
                            INSERT INTO metrics (
                                id, trial_id, evaluation_id, name, scope, fold_index,
                                value, direction, reason, details_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(trial_id, scope, name, fold_index, IFNULL(evaluation_id, ''))
                            DO UPDATE SET value = excluded.value, reason = excluded.reason;
                            """,
                            (
                                str(__import__("uuid").uuid4()),
                                trial.trial_id,
                                None,  # evaluation_id
                                metric.name,
                                metric.scope.value,
                                metric.fold_index if metric.scope == MetricScope.CV_FOLD else -1,
                                metric.value,
                                metric.direction.value,
                                metric.reason,
                                metric.details_json,
                            ),
                        )

                # Save model selection if present
                if summary.selected_trial_id:
                    conn.execute(
                        """
                        INSERT INTO model_selections (experiment_id, trial_id, selection_reason, selected_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(experiment_id) DO UPDATE SET
                            trial_id = excluded.trial_id,
                            selection_reason = excluded.selection_reason,
                            selected_at = excluded.selected_at;
                        """,
                        (
                            summary.id,
                            summary.selected_trial_id,
                            summary.selection_reason or "",
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )
        finally:
            conn.close()

    def get_by_submission_token(self, submission_token: str) -> Optional[ExperimentSummary]:
        """Get an experiment by submission token."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT id, project_id, dataset_id, split_id, task, name, status,
                       submission_token, config_json, comparison_key, random_seed,
                       primary_metric, started_at, finished_at, error_json
                FROM experiments WHERE submission_token = ?;
                """,
                (submission_token,),
            ).fetchone()
            if row:
                return self._build_experiment_summary(row, conn)
            return None
        finally:
            conn.close()

    def get_by_id(self, experiment_id: str) -> Optional[ExperimentSummary]:
        """Get an experiment by ID with trials and metrics."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT id, project_id, dataset_id, split_id, task, name, status,
                       submission_token, config_json, comparison_key, random_seed,
                       primary_metric, started_at, finished_at, error_json
                FROM experiments WHERE id = ?;
                """,
                (experiment_id,),
            ).fetchone()
            if row:
                return self._build_experiment_summary(row, conn)
            return None
        finally:
            conn.close()

    def list_by_project(self, project_id: str) -> List[ExperimentSummary]:
        """List all experiments for a project."""
        conn = get_connection(self.db_path)
        try:
            rows = conn.execute(
                """
                SELECT id, project_id, dataset_id, split_id, task, name, status,
                       submission_token, config_json, comparison_key, random_seed,
                       primary_metric, started_at, finished_at, error_json
                FROM experiments WHERE project_id = ? ORDER BY started_at DESC;
                """,
                (project_id,),
            ).fetchall()

            return [self._build_experiment_summary(row, conn) for row in rows]
        finally:
            conn.close()

    def _build_experiment_summary(
        self, row: sqlite3.Row, conn: sqlite3.Connection
    ) -> ExperimentSummary:
        """Build ExperimentSummary from a database row."""
        experiment_id = row["id"]

        # Load trials
        trial_rows = conn.execute(
            """
            SELECT id, algorithm_id, is_baseline, parameters_json, status,
                   fit_duration_seconds, warnings_json, error_json, created_at
            FROM trials WHERE experiment_id = ?;
            """,
            (experiment_id,),
        ).fetchall()

        trials = []
        for trial_row in trial_rows:
            trial_id = trial_row["id"]

            # Load metrics for this trial
            metric_rows = conn.execute(
                """
                SELECT name, scope, fold_index, value, direction, reason, details_json
                FROM metrics WHERE trial_id = ?;
                """,
                (trial_id,),
            ).fetchall()

            metrics = [
                MetricRecord(
                    id=str(__import__("uuid").uuid4()),
                    trial_id=trial_id,
                    evaluation_id=None,
                    name=m["name"],
                    scope=MetricScope(m["scope"]),
                    fold_index=m["fold_index"],
                    value=m["value"],
                    direction=MetricDirection(m["direction"]),
                    reason=m["reason"],
                    details_json=m["details_json"],
                )
                for m in metric_rows
            ]

            # Compute primary CV mean if available
            primary_cv_mean = None
            primary_cv_std = None
            primary_metrics = [
                m for m in metrics if m.scope == MetricScope.CV_MEAN and m.name == row["primary_metric"]
            ]
            if primary_metrics:
                primary_cv_mean = primary_metrics[0].value

            trials.append(
                TrialResult(
                    trial_id=trial_id,
                    experiment_id=experiment_id,
                    algorithm_id=trial_row["algorithm_id"],
                    is_baseline=trial_row["is_baseline"] == 1,
                    parameters=json.loads(trial_row["parameters_json"]),
                    status=trial_row["status"],
                    fit_duration_seconds=trial_row["fit_duration_seconds"] or 0.0,
                    warnings=json.loads(trial_row["warnings_json"]),
                    error=json.loads(trial_row["error_json"]).get("error") if trial_row["error_json"] else None,
                    metrics=metrics,
                    primary_cv_mean=primary_cv_mean,
                    primary_cv_std=primary_cv_std,
                )
            )

        # Load model selection
        selection_row = conn.execute(
            "SELECT trial_id, selection_reason FROM model_selections WHERE experiment_id = ?;",
            (experiment_id,),
        ).fetchone()

        return ExperimentSummary(
            id=experiment_id,
            project_id=row["project_id"],
            dataset_id=row["dataset_id"],
            split_id=row["split_id"],
            task=TaskType(row["task"]),
            name=row["name"],
            status=row["status"],
            submission_token=row["submission_token"],
            config_json=row["config_json"],
            comparison_key=row["comparison_key"],
            random_seed=row["random_seed"],
            primary_metric=row["primary_metric"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            trials=trials,
            selected_trial_id=selection_row["trial_id"] if selection_row else None,
            selection_reason=selection_row["selection_reason"] if selection_row else None,
        )


class EvaluationRepository:
    """Repository for holdout evaluation persistence."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def save_evaluation(self, evaluation: HoldoutEvaluation) -> None:
        """Save or update a holdout evaluation."""
        conn = get_connection(self.db_path)
        try:
            with conn:
                # Upsert evaluation
                conn.execute(
                    """
                    INSERT INTO evaluations (
                        id, experiment_id, trial_id, split_id, scope,
                        holdout_previously_exposed, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(experiment_id, scope) DO UPDATE SET
                        trial_id = excluded.trial_id,
                        split_id = excluded.split_id,
                        holdout_previously_exposed = excluded.holdout_previously_exposed;
                    """,
                    (
                        evaluation.id,
                        evaluation.experiment_id,
                        evaluation.trial_id,
                        evaluation.split_id,
                        evaluation.scope,
                        1 if evaluation.holdout_previously_exposed else 0,
                        evaluation.created_at,
                    ),
                )

                # Save evaluation metrics
                for metric in evaluation.metrics:
                    conn.execute(
                        """
                        INSERT INTO metrics (
                            id, trial_id, evaluation_id, name, scope, fold_index,
                            value, direction, reason, details_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(trial_id, scope, name, fold_index, IFNULL(evaluation_id, ''))
                        DO UPDATE SET value = excluded.value, reason = excluded.reason;
                        """,
                        (
                            str(__import__("uuid").uuid4()),
                            evaluation.trial_id,
                            evaluation.id,
                            metric.name,
                            metric.scope.value,
                            -1,  # fold_index not used for holdout
                            metric.value,
                            metric.direction.value,
                            metric.reason,
                            metric.details_json,
                        ),
                    )
        finally:
            conn.close()

    def get_evaluation(self, experiment_id: str) -> Optional[HoldoutEvaluation]:
        """Get the holdout evaluation for an experiment."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT id, experiment_id, trial_id, split_id, scope,
                       holdout_previously_exposed, created_at
                FROM evaluations WHERE experiment_id = ? AND scope = 'holdout';
                """,
                (experiment_id,),
            ).fetchone()
            if row:
                # Load evaluation metrics
                metric_rows = conn.execute(
                    """
                    SELECT name, scope, fold_index, value, direction, reason, details_json
                    FROM metrics WHERE evaluation_id = ?;
                    """,
                    (row["id"],),
                ).fetchall()

                metrics = [
                    MetricRecord(
                        id=str(__import__("uuid").uuid4()),
                        trial_id=row["trial_id"],
                        evaluation_id=row["id"],
                        name=m["name"],
                        scope=MetricScope(m["scope"]),
                        fold_index=m["fold_index"],
                        value=m["value"],
                        direction=MetricDirection(m["direction"]),
                        reason=m["reason"],
                        details_json=m["details_json"],
                    )
                    for m in metric_rows
                ]

                return HoldoutEvaluation(
                    id=row["id"],
                    experiment_id=row["experiment_id"],
                    trial_id=row["trial_id"],
                    split_id=row["split_id"],
                    scope=row["scope"],
                    holdout_previously_exposed=row["holdout_previously_exposed"] == 1,
                    created_at=row["created_at"],
                    metrics=metrics,
                    confusion_matrix=None,  # Loaded separately if needed
                    class_labels=None,  # Loaded separately if needed
                )
            return None
        finally:
            conn.close()

    def is_split_holdout_exposed(self, split_id: str) -> bool:
        """Check if a split has been used in any prior holdout evaluation."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT COUNT(*) as count FROM evaluations
                WHERE split_id = ? AND scope = 'holdout';
                """,
                (split_id,),
            ).fetchone()
            return row["count"] > 0
        finally:
            conn.close()
