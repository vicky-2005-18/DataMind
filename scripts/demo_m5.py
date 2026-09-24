"""Run a real offline M5 clustering and playground demonstration."""

from __future__ import annotations

import json
import uuid

from datamind.config import get_settings
from datamind.contracts import DemoDatasetKind
from datamind.services.clustering import ClusteringService
from datamind.services.datasets import DatasetService
from datamind.services.playground import run_classification_playground, run_clustering_playground
from datamind.services.projects import ProjectService
from datamind.storage.database import run_migrations


def main() -> None:
    settings = get_settings()
    settings.ensure_directories()
    run_migrations(settings.db_path)
    project = ProjectService().create_project(f"M5 Demo {uuid.uuid4().hex[:8]}")
    dataset_service = DatasetService()
    dataset = dataset_service.load_demo(project.id, DemoDatasetKind.SYNTHETIC_BLOBS, seed=42)
    clustering = ClusteringService(dataset_service=dataset_service).run_experiment(
        project_id=project.id,
        dataset_id=dataset.id,
        experiment_name="M5 seeded blobs",
        feature_names=["feature_1", "feature_2", "feature_3", "feature_4"],
        k=3,
        seed=42,
    )
    tree = run_classification_playground("decision_tree", tree_depth=4, seed=42)
    knn = run_classification_playground("knn", n_neighbors=7, seed=42)
    playground_clusters = run_clustering_playground(cluster_count=4, seed=42)
    print(
        json.dumps(
            {
                "project_id": project.id,
                "dataset_id": dataset.id,
                "experiment_id": clustering.experiment.id,
                "cluster_sizes": clustering.cluster_sizes,
                "inertia": clustering.inertia,
                "silhouette": clustering.silhouette,
                "silhouette_sample_size": clustering.silhouette_sample_size,
                "elbow_points": len(clustering.elbow_points),
                "trial_count": len(clustering.experiment.trials),
                "artifacts": clustering.artifact_paths,
                "tree_mesh": [len(tree.mesh_values), len(tree.mesh_values[0])],
                "knn_mesh": [len(knn.mesh_values), len(knn.mesh_values[0])],
                "playground_cluster_count": len(set(playground_clusters.labels)),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
