"""Offline demonstration dataset generators."""

from __future__ import annotations

import io
from typing import Tuple

import pandas as pd
from sklearn.datasets import load_iris, make_blobs, make_regression

from datamind.contracts import DemoDatasetKind, ErrorCode, ServiceError


def generate_demo_csv(demo_kind: DemoDatasetKind, seed: int = 42) -> Tuple[str, bytes, dict]:
    """Generate offline demo dataset as CSV bytes with source metadata."""
    if demo_kind == DemoDatasetKind.IRIS:
        iris = load_iris(as_frame=True)
        df: pd.DataFrame = iris.frame.copy()
        # Map target numbers to species names for readable classification
        target_names = {0: "setosa", 1: "versicolor", 2: "virginica"}
        df["target"] = df["target"].map(target_names)
        df.rename(
            columns={
                "sepal length (cm)": "sepal_length",
                "sepal width (cm)": "sepal_width",
                "petal length (cm)": "petal_length",
                "petal width (cm)": "petal_width",
                "target": "species",
            },
            inplace=True,
        )
        display_name = "Iris Flower Classification Demo"
        source_meta = {
            "demo_kind": "iris",
            "task_hint": "classification",
            "target_hint": "species",
            "samples": len(df),
            "features": len(df.columns) - 1,
            "offline": True,
        }

    elif demo_kind == DemoDatasetKind.SYNTHETIC_REGRESSION:
        X, y = make_regression(
            n_samples=500,
            n_features=6,
            n_informative=4,
            noise=10.0,
            random_state=seed,
        )
        df = pd.DataFrame(
            X.round(4),
            columns=[f"feature_{index}" for index in range(1, 7)],
        )
        df["target"] = y.round(4)
        display_name = "Synthetic Regression Demo"
        source_meta = {
            "demo_kind": "synthetic_regression",
            "task_hint": "regression",
            "target_hint": "target",
            "seed": seed,
            "samples": len(df),
            "features": 6,
            "informative_features": 4,
            "noise": 10.0,
            "offline": True,
        }

    elif demo_kind == DemoDatasetKind.SYNTHETIC_BLOBS:
        X, _ = make_blobs(
            n_samples=600,
            n_features=4,
            centers=3,
            cluster_std=1.0,
            random_state=seed,
        )
        df = pd.DataFrame(
            X.round(4),
            columns=[f"feature_{index}" for index in range(1, 5)],
        )
        display_name = "Synthetic 4D Blobs Clustering Demo"
        source_meta = {
            "demo_kind": "synthetic_blobs",
            "task_hint": "clustering",
            "target_hint": None,
            "seed": seed,
            "samples": len(df),
            "features": 4,
            "centers": 3,
            "cluster_std": 1.0,
            "offline": True,
        }
    else:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            f"Unknown demo kind '{demo_kind}'.",
        )

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    csv_bytes = buffer.getvalue().encode("utf-8")

    return display_name, csv_bytes, source_meta
