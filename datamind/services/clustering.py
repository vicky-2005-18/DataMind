"""Bounded numeric K-Means clustering with persisted diagnostics."""

from __future__ import annotations

import datetime
import hashlib
import json
import time
import uuid
from typing import Optional

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from datamind.config import get_settings
from datamind.contracts import (
    ClusteringResult,
    ErrorCode,
    ExperimentSummary,
    MetricDirection,
    MetricRecord,
    MetricScope,
    ServiceError,
    TaskType,
    TrialResult,
)
from datamind.services.datasets import DatasetService
from datamind.storage.artifacts import compute_sha256_file, safe_relative_path, write_atomic_bytes
from datamind.storage.database import get_connection
from datamind.storage.experiment_repos import ExperimentRepository
from datamind.storage.locks import WorkspaceLock


def compute_silhouette_diagnostic(
    transformed: np.ndarray,
    labels: np.ndarray,
    seed: int,
    max_rows: int = 2000,
) -> tuple[Optional[float], Optional[str], int]:
    """Compute a bounded silhouette score or return a precise undefined reason."""
    sample_size = min(max_rows, len(transformed))
    if not 2 <= len(np.unique(labels)) <= len(transformed) - 1:
        return None, "Silhouette requires between 2 and n_rows - 1 observed clusters.", sample_size
    if len(transformed) > sample_size:
        rng = np.random.default_rng(seed)
        sample_indices = np.sort(rng.choice(len(transformed), sample_size, replace=False))
        sample_x = transformed[sample_indices]
        sample_labels = labels[sample_indices]
    else:
        sample_x = transformed
        sample_labels = labels
    if not 2 <= len(np.unique(sample_labels)) <= len(sample_x) - 1:
        return None, "The seeded silhouette sample did not contain a valid number of clusters.", sample_size
    return float(silhouette_score(sample_x, sample_labels)), None, sample_size


class ClusteringService:
    """Fit, validate, and persist one selected-k K-Means trial per experiment."""

    def __init__(
        self,
        dataset_service: Optional[DatasetService] = None,
        experiment_repo: Optional[ExperimentRepository] = None,
        lock: Optional[WorkspaceLock] = None,
    ):
        settings = get_settings()
        self.dataset_service = dataset_service or DatasetService()
        self.experiment_repo = experiment_repo or ExperimentRepository(settings.db_path)
        self.lock = lock or WorkspaceLock(settings.locks_dir / "workspace.lock")

    def run_experiment(
        self,
        project_id: str,
        dataset_id: str,
        experiment_name: str,
        feature_names: list[str],
        k: int,
        seed: int = 42,
        submission_token: Optional[str] = None,
    ) -> ClusteringResult:
        dataset = self.dataset_service.get_dataset(dataset_id)
        if dataset is None or dataset.project_id != project_id:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                "The selected dataset does not belong to the active project.",
                field="dataset_id",
            )
        if len(feature_names) < 2:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                "Select at least two numeric features for clustering.",
                field="feature_names",
            )
        if len(set(feature_names)) != len(feature_names):
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                "Clustering feature names must be unique.",
                field="feature_names",
            )

        frame = self.dataset_service.load_dataframe(dataset_id)
        missing = [name for name in feature_names if name not in frame.columns]
        if missing:
            raise ServiceError(
                ErrorCode.UNSUPPORTED_FEATURE,
                f"Unknown clustering features: {missing}.",
                field="feature_names",
            )
        if len(frame) < 30:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                "Clustering requires at least 30 rows.",
            )

        selected = frame[feature_names].copy()
        invalid = [name for name in feature_names if not np.issubdtype(selected[name].dtype, np.number)]
        if invalid:
            raise ServiceError(
                ErrorCode.UNSUPPORTED_FEATURE,
                f"K-Means supports numeric features only: {invalid}.",
                field="feature_names",
            )
        if np.isinf(selected.to_numpy(dtype=float, na_value=np.nan)).any():
            raise ServiceError(
                ErrorCode.UNSUPPORTED_FEATURE,
                "Clustering features must contain finite values or missing values.",
            )

        all_missing = [name for name in feature_names if selected[name].isna().all()]
        constant = [name for name in feature_names if name not in all_missing and selected[name].nunique(dropna=True) <= 1]
        usable = [name for name in feature_names if name not in all_missing and name not in constant]
        if len(usable) < 2:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                "At least two nonconstant, non-all-missing numeric features are required.",
                details={"all_missing": all_missing, "constant": constant},
            )

        config = {
            "schema_version": 1,
            "task": "clustering",
            "dataset_id": dataset_id,
            "feature_names": usable,
            "excluded_all_missing": all_missing,
            "excluded_constant": constant,
            "preprocessing": {"imputer": "median", "scaler": "standard"},
            "model": {"algorithm_id": "kmeans", "parameters": {"k": k, "n_init": 10, "max_iter": 300}},
            "random_seed": seed,
            "primary_metric": "silhouette",
        }
        config_json = json.dumps(config, sort_keys=True)
        token = submission_token or hashlib.sha256(
            json.dumps({"project_id": project_id, "name": experiment_name, "config": config}, sort_keys=True).encode()
        ).hexdigest()
        cached = self.experiment_repo.get_by_submission_token(token)
        if cached is not None:
            return self.load_result(cached.id)

        with self.lock.acquire():
            cached = self.experiment_repo.get_by_submission_token(token)
            if cached is not None:
                return self.load_result(cached.id)

            experiment_id = str(uuid.uuid4())
            trial_id = str(uuid.uuid4())
            started = datetime.datetime.now(datetime.timezone.utc).isoformat()
            start_clock = time.perf_counter()

            preprocess = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            )
            transformed = preprocess.fit_transform(selected[usable])
            unique_rows = np.unique(transformed, axis=0).shape[0]
            max_k = min(10, unique_rows - 1, len(transformed) - 1)
            if max_k < 2 or k < 2 or k > max_k:
                raise ServiceError(
                    ErrorCode.INVALID_MODEL_CONFIG,
                    f"k must be between 2 and {max_k} for the selected data.",
                    field="k",
                    details={"max_k": max_k, "unique_transformed_rows": unique_rows},
                )

            elbow_points: list[dict[str, float]] = []
            for candidate_k in range(1, max_k + 1):
                sweep_model = KMeans(
                    n_clusters=candidate_k,
                    n_init=10,
                    max_iter=300,
                    random_state=seed,
                )
                sweep_model.fit(transformed)
                elbow_points.append({"k": float(candidate_k), "inertia": float(sweep_model.inertia_)})

            model = KMeans(n_clusters=k, n_init=10, max_iter=300, random_state=seed)
            labels = model.fit_predict(transformed)
            observed_clusters = np.unique(labels)
            warnings: list[str] = []
            if len(observed_clusters) < k:
                warnings.append(f"K-Means produced {len(observed_clusters)} distinct clusters for requested k={k}.")

            silhouette_value, silhouette_reason, silhouette_sample_size = compute_silhouette_diagnostic(
                transformed,
                labels,
                seed,
            )

            pca = PCA(n_components=2)
            projection = pca.fit_transform(transformed)
            sizes = {int(label): int(np.sum(labels == label)) for label in observed_clusters}
            duration = time.perf_counter() - start_clock

            experiment_dir = get_settings().experiments_dir / experiment_id
            experiment_dir.mkdir(parents=True, exist_ok=False)
            pipeline = Pipeline([("imputer", preprocess["imputer"]), ("scaler", preprocess["scaler"]), ("model", model)])
            model_path = experiment_dir / "kmeans.joblib"
            joblib.dump(pipeline, model_path)

            diagnostic = {
                "scope": "clustering",
                "feature_names": usable,
                "row_count": len(selected),
                "k": k,
                "seed": seed,
                "cluster_labels": labels.astype(int).tolist(),
                "cluster_sizes": sizes,
                "inertia": float(model.inertia_),
                "silhouette": silhouette_value,
                "silhouette_reason": silhouette_reason,
                "silhouette_sample_size": silhouette_sample_size,
                "elbow_points": elbow_points,
                "pca_coordinates": projection.tolist(),
                "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
                "warnings": warnings,
            }
            diagnostic_path = experiment_dir / "clustering_diagnostics.json"
            write_atomic_bytes(diagnostic_path, json.dumps(diagnostic, indent=2, sort_keys=True).encode())
            config_path = experiment_dir / "config.json"
            write_atomic_bytes(config_path, config_json.encode())

            metrics = [
                MetricRecord(
                    id=str(uuid.uuid4()),
                    trial_id=trial_id,
                    name="inertia",
                    scope=MetricScope.CLUSTERING,
                    value=float(model.inertia_),
                    direction=MetricDirection.MINIMIZE,
                ),
                MetricRecord(
                    id=str(uuid.uuid4()),
                    trial_id=trial_id,
                    name="silhouette",
                    scope=MetricScope.CLUSTERING,
                    value=silhouette_value,
                    reason=silhouette_reason,
                    direction=MetricDirection.MAXIMIZE,
                    details_json=json.dumps({"sample_size": silhouette_sample_size, "space": "scaled_modeling_features"}),
                ),
            ]
            trial = TrialResult(
                trial_id=trial_id,
                experiment_id=experiment_id,
                algorithm_id="kmeans",
                is_baseline=False,
                parameters={"k": k, "n_init": 10, "max_iter": 300, "seed": seed},
                status="completed",
                fit_duration_seconds=duration,
                warnings=warnings,
                metrics=metrics,
            )
            finished = datetime.datetime.now(datetime.timezone.utc).isoformat()
            summary = ExperimentSummary(
                id=experiment_id,
                project_id=project_id,
                dataset_id=dataset_id,
                split_id=None,
                task=TaskType.CLUSTERING,
                name=experiment_name,
                status="completed",
                submission_token=token,
                config_json=config_json,
                comparison_key=hashlib.sha256(
                    json.dumps({"dataset_id": dataset_id, "features": usable, "scaling": "standard"}, sort_keys=True).encode()
                ).hexdigest(),
                random_seed=seed,
                primary_metric="silhouette",
                started_at=started,
                finished_at=finished,
                trials=[trial],
                selected_trial_id=trial_id,
                selection_reason="User-confirmed exploratory k; not an automatic optimum.",
            )
            self.experiment_repo.save_experiment(summary)

            artifact_paths = {
                "model": safe_relative_path(get_settings().storage_dir, model_path),
                "diagnostics": safe_relative_path(get_settings().storage_dir, diagnostic_path),
                "config": safe_relative_path(get_settings().storage_dir, config_path),
            }
            self._register_artifacts(experiment_id, trial_id, artifact_paths)
            return ClusteringResult(
                experiment=summary,
                feature_names=usable,
                cluster_labels=diagnostic["cluster_labels"],
                cluster_sizes=sizes,
                inertia=diagnostic["inertia"],
                silhouette=silhouette_value,
                silhouette_reason=silhouette_reason,
                silhouette_sample_size=silhouette_sample_size,
                pca_coordinates=diagnostic["pca_coordinates"],
                pca_explained_variance=diagnostic["pca_explained_variance"],
                elbow_points=elbow_points,
                artifact_paths=artifact_paths,
                warnings=warnings,
            )

    def _register_artifacts(self, experiment_id: str, trial_id: str, artifact_paths: dict[str, str]) -> None:
        settings = get_settings()
        conn = get_connection(settings.db_path)
        try:
            with conn:
                for kind, relative_path in artifact_paths.items():
                    absolute_path = settings.storage_dir / relative_path
                    conn.execute(
                        """
                        INSERT INTO artifacts
                        (id, experiment_id, trial_id, kind, relative_path, sha256, size_bytes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            str(uuid.uuid4()),
                            experiment_id,
                            trial_id,
                            f"clustering_{kind}",
                            relative_path,
                            compute_sha256_file(absolute_path),
                            absolute_path.stat().st_size,
                            datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        ),
                    )
        finally:
            conn.close()

    def load_result(self, experiment_id: str) -> ClusteringResult:
        summary = self.experiment_repo.get_by_id(experiment_id)
        if summary is None or summary.task != TaskType.CLUSTERING:
            raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Clustering experiment not found.")
        diagnostic_path = get_settings().experiments_dir / experiment_id / "clustering_diagnostics.json"
        if not diagnostic_path.exists():
            raise ServiceError(ErrorCode.MODEL_UNAVAILABLE, "Clustering diagnostic artifact is missing.")
        data = json.loads(diagnostic_path.read_text(encoding="utf-8"))
        experiment_dir = diagnostic_path.parent
        return ClusteringResult(
            experiment=summary,
            feature_names=data["feature_names"],
            cluster_labels=data["cluster_labels"],
            cluster_sizes={int(key): value for key, value in data["cluster_sizes"].items()},
            inertia=data["inertia"],
            silhouette=data["silhouette"],
            silhouette_reason=data["silhouette_reason"],
            silhouette_sample_size=data["silhouette_sample_size"],
            pca_coordinates=data["pca_coordinates"],
            pca_explained_variance=data["pca_explained_variance"],
            elbow_points=data["elbow_points"],
            artifact_paths={
                "model": safe_relative_path(get_settings().storage_dir, experiment_dir / "kmeans.joblib"),
                "diagnostics": safe_relative_path(get_settings().storage_dir, diagnostic_path),
                "config": safe_relative_path(get_settings().storage_dir, experiment_dir / "config.json"),
            },
            warnings=data["warnings"],
        )
