"""M5 verification for clustering and fitted educational playgrounds."""

from __future__ import annotations

import json
import uuid

import numpy as np
import pytest

from datamind.contracts import DemoDatasetKind, ErrorCode, ServiceError
from datamind.services.clustering import ClusteringService
from datamind.services.datasets import DatasetService
from datamind.services.playground import run_classification_playground, run_clustering_playground
from datamind.services.projects import ProjectService
from datamind.storage.database import get_connection


def _blobs_run(migrated_db):
    project = ProjectService().create_project(f"M5 {uuid.uuid4().hex[:8]}")
    dataset_service = DatasetService()
    dataset = dataset_service.load_demo(project.id, DemoDatasetKind.SYNTHETIC_BLOBS, seed=42)
    service = ClusteringService(dataset_service=dataset_service)
    result = service.run_experiment(
        project_id=project.id,
        dataset_id=dataset.id,
        experiment_name="Seeded blobs",
        feature_names=["feature_1", "feature_2", "feature_3", "feature_4"],
        k=3,
        seed=42,
    )
    return result, dataset, service


def test_t35_seeded_kmeans_persistence(migrated_db):
    result, dataset, service = _blobs_run(migrated_db)
    assert np.isfinite(result.inertia)
    assert sum(result.cluster_sizes.values()) == dataset.row_count
    assert result.silhouette is not None and np.isfinite(result.silhouette)
    assert result.silhouette_sample_size == dataset.row_count
    assert len(result.experiment.trials) == 1
    assert result.experiment.trials[0].algorithm_id == "kmeans"
    assert result.experiment.split_id is None
    config = json.loads(result.experiment.config_json)
    assert config["random_seed"] == 42
    assert config["preprocessing"] == {"imputer": "median", "scaler": "standard"}
    assert config["feature_names"] == ["feature_1", "feature_2", "feature_3", "feature_4"]
    assert len(result.elbow_points) >= 3
    assert service.load_result(result.experiment.id).cluster_sizes == result.cluster_sizes

    conn = get_connection(migrated_db)
    try:
        trial_count = conn.execute(
            "SELECT COUNT(*) FROM trials WHERE experiment_id = ?", (result.experiment.id,)
        ).fetchone()[0]
        artifacts = conn.execute(
            "SELECT kind, sha256 FROM artifacts WHERE experiment_id = ?", (result.experiment.id,)
        ).fetchall()
    finally:
        conn.close()
    assert trial_count == 1
    assert {row["kind"] for row in artifacts} == {
        "clustering_model",
        "clustering_diagnostics",
        "clustering_config",
    }
    assert all(len(row["sha256"]) == 64 for row in artifacts)


def test_t36_k_and_silhouette_guards(migrated_db):
    project = ProjectService().create_project(f"M5 guards {uuid.uuid4().hex[:8]}")
    dataset_service = DatasetService()
    dataset = dataset_service.load_demo(project.id, DemoDatasetKind.SYNTHETIC_BLOBS, seed=42)
    service = ClusteringService(dataset_service=dataset_service)

    with pytest.raises(ServiceError) as invalid_k:
        service.run_experiment(project.id, dataset.id, "invalid", ["feature_1", "feature_2"], k=20)
    assert invalid_k.value.code == ErrorCode.INVALID_MODEL_CONFIG

    from datamind.services.clustering import compute_silhouette_diagnostic

    points = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
    value, reason, sample_size = compute_silhouette_diagnostic(points, np.zeros(3, dtype=int), seed=42)
    assert value is None
    assert "2 and n_rows - 1" in reason
    assert sample_size == 3


def test_t37_silhouette_uses_scaled_space_not_pca(migrated_db):
    result, _dataset, _service = _blobs_run(migrated_db)
    assert len(result.pca_coordinates[0]) == 2
    diagnostic_path = next(
        path for key, path in result.artifact_paths.items() if key == "diagnostics"
    )
    from datamind.config import get_settings

    diagnostic = json.loads((get_settings().storage_dir / diagnostic_path).read_text(encoding="utf-8"))
    assert diagnostic["silhouette"] == result.silhouette
    trial_metric = next(
        metric for metric in result.experiment.trials[0].metrics if metric.name == "silhouette"
    )
    details = json.loads(trial_metric.details_json)
    assert details["space"] == "scaled_modeling_features"
    assert "pca" not in details["space"].lower()


def test_t38_real_parameter_changes_update_outputs():
    shallow = run_classification_playground("decision_tree", tree_depth=1, seed=42)
    deep = run_classification_playground("decision_tree", tree_depth=8, seed=42)
    assert shallow.mesh_values != deep.mesh_values

    knn_small = run_classification_playground("knn", n_neighbors=1, seed=42)
    knn_large = run_classification_playground("knn", n_neighbors=25, seed=42)
    assert knn_small.mesh_values != knn_large.mesh_values

    clusters_two = run_clustering_playground(cluster_count=2, seed=42)
    clusters_five = run_clustering_playground(cluster_count=5, seed=42)
    assert len(set(clusters_two.labels)) == 2
    assert len(set(clusters_five.labels)) == 5
    assert clusters_two.labels != clusters_five.labels
