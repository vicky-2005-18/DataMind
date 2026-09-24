"""Unit tests for offline demo dataset generators (T06)."""

from __future__ import annotations

import pandas as pd

from datamind.contracts import DemoDatasetKind
from datamind.data.demos import generate_demo_csv
from datamind.data.ingestion import validate_and_parse_csv


def test_t06_iris_demo_offline() -> None:
    """T06: Iris demo loads offline with deterministic metadata, 150 rows, and 3 classes."""
    display_name, raw_bytes, meta = generate_demo_csv(DemoDatasetKind.IRIS)

    assert "Iris" in display_name
    assert meta["offline"] is True
    assert meta["task_hint"] == "classification"
    assert meta["target_hint"] == "species"

    parsed = validate_and_parse_csv(raw_bytes, filename="iris.csv")
    df = parsed.df

    assert len(df) == 150
    assert set(df.columns) == {"sepal_length", "sepal_width", "petal_length", "petal_width", "species"}
    assert set(df["species"].unique()) == {"setosa", "versicolor", "virginica"}
    # 50 samples per class in Iris
    assert (df["species"].value_counts() == 50).all()


def test_t06_synthetic_regression_deterministic() -> None:
    """T06: Synthetic regression demo is deterministic under fixed seed."""
    _, bytes1, meta1 = generate_demo_csv(DemoDatasetKind.SYNTHETIC_REGRESSION, seed=42)
    _, bytes2, meta2 = generate_demo_csv(DemoDatasetKind.SYNTHETIC_REGRESSION, seed=42)

    assert bytes1 == bytes2
    assert meta1["seed"] == 42
    assert meta1["task_hint"] == "regression"

    parsed = validate_and_parse_csv(bytes1, filename="reg.csv")
    df = parsed.df
    assert len(df) == 500
    assert "target" in df.columns
    assert pd.api.types.is_numeric_dtype(df["target"])


def test_t06_synthetic_blobs_unsupervised() -> None:
    """T06: Synthetic blobs demo generates 3D clustering data with no target."""
    _, raw_bytes, meta = generate_demo_csv(DemoDatasetKind.SYNTHETIC_BLOBS, seed=42)

    assert meta["task_hint"] == "clustering"
    assert meta["target_hint"] is None

    parsed = validate_and_parse_csv(raw_bytes, filename="blobs.csv")
    df = parsed.df
    assert len(df) == 600
    assert len(df.columns) == 4
    assert "target" not in df.columns
