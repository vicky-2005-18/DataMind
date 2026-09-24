"""Seeded educational playgrounds backed by real fitted estimators."""

from __future__ import annotations

from typing import Literal

import numpy as np
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs, make_moons
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier

from datamind.contracts import ErrorCode, PlaygroundResult, ServiceError


def run_classification_playground(
    algorithm: Literal["decision_tree", "knn"],
    sample_count: int = 300,
    noise: float = 0.25,
    seed: int = 42,
    tree_depth: int = 3,
    n_neighbors: int = 5,
) -> PlaygroundResult:
    """Fit a classifier on seeded moons and return a bounded real decision mesh."""
    if not 100 <= sample_count <= 1000:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Sample count must be between 100 and 1,000.")
    if not 0.0 <= noise <= 0.5:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Noise must be between 0 and 0.5.")
    if algorithm == "decision_tree":
        if not 1 <= tree_depth <= 20:
            raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Tree depth must be between 1 and 20.")
        estimator = DecisionTreeClassifier(max_depth=tree_depth, random_state=seed)
        parameters = {"tree_depth": tree_depth, "sample_count": sample_count, "noise": noise}
        explanation = "A decision tree partitions the plane into axis-aligned regions; greater depth permits finer regions."
        limitation = "Deep trees can memorize noise and produce unstable boundaries."
    elif algorithm == "knn":
        if not 1 <= n_neighbors <= 25 or n_neighbors > sample_count:
            raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "kNN k must be between 1 and 25 and no larger than the sample count.")
        estimator = KNeighborsClassifier(n_neighbors=n_neighbors)
        parameters = {"n_neighbors": n_neighbors, "sample_count": sample_count, "noise": noise}
        explanation = "kNN predicts from nearby fitted examples; larger k produces smoother local voting regions."
        limitation = "Distances are sensitive to scaling and can weaken in high dimensions."
    else:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, f"Unsupported playground algorithm: {algorithm}.")

    points, labels = make_moons(n_samples=sample_count, noise=noise, random_state=seed)
    estimator.fit(points, labels)
    padding = 0.5
    x_axis = np.linspace(points[:, 0].min() - padding, points[:, 0].max() + padding, 180)
    y_axis = np.linspace(points[:, 1].min() - padding, points[:, 1].max() + padding, 180)
    mesh_x, mesh_y = np.meshgrid(x_axis, y_axis)
    mesh = np.column_stack([mesh_x.ravel(), mesh_y.ravel()])
    mesh_values = estimator.predict(mesh).reshape(mesh_x.shape)
    return PlaygroundResult(
        kind=algorithm,
        seed=seed,
        parameters=parameters,
        points=points.tolist(),
        labels=labels.astype(int).tolist(),
        mesh_x=mesh_x.tolist(),
        mesh_y=mesh_y.tolist(),
        mesh_values=mesh_values.astype(float).tolist(),
        explanation=explanation,
        limitation=limitation,
    )


def run_clustering_playground(
    sample_count: int = 300,
    cluster_count: int = 3,
    noise: float = 1.0,
    seed: int = 42,
) -> PlaygroundResult:
    """Fit K-Means on seeded blobs and return actual cluster assignments."""
    if not 100 <= sample_count <= 1000:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Sample count must be between 100 and 1,000.")
    if not 2 <= cluster_count <= 10 or cluster_count >= sample_count:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Cluster k must be between 2 and 10 and smaller than the sample count.")
    if not 0.1 <= noise <= 3.0:
        raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, "Cluster spread must be between 0.1 and 3.0.")

    points, _ = make_blobs(
        n_samples=sample_count,
        centers=4,
        cluster_std=noise,
        random_state=seed,
    )
    estimator = KMeans(n_clusters=cluster_count, n_init=10, random_state=seed)
    labels = estimator.fit_predict(points)
    return PlaygroundResult(
        kind="kmeans",
        seed=seed,
        parameters={"cluster_count": cluster_count, "sample_count": sample_count, "noise": noise},
        points=points.tolist(),
        labels=labels.astype(int).tolist(),
        explanation="K-Means alternates point assignment and centroid updates to reduce within-cluster squared distance.",
        limitation="The chosen k is exploratory, and K-Means favors compact roughly spherical groups.",
    )
