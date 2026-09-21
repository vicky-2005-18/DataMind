"""Integration tests for dataset persistence, immutability, and hashing (T07)."""

from __future__ import annotations

from pathlib import Path

import pytest

from datamind.contracts import DemoDatasetKind, ErrorCode, ServiceError
from datamind.services.datasets import DatasetService
from datamind.services.projects import ProjectService


def test_t07_dataset_import_and_immutability(migrated_db: Path) -> None:
    """T07: Imported CSV is persisted as immutable raw bytes with verified SHA-256."""
    project_service = ProjectService()
    project = project_service.create_project("Dataset Test Lab")

    dataset_service = DatasetService()

    csv_bytes = b"feature_x,feature_y,target\n1.0,2.0,10.0\n3.0,4.0,20.0\n"
    ds1 = dataset_service.import_csv(
        project_id=project.id,
        raw_bytes=csv_bytes,
        display_name="v1.csv",
    )

    assert ds1.id is not None
    assert ds1.project_id == project.id
    assert ds1.row_count == 2
    assert ds1.column_count == 3
    assert ds1.raw_sha256 is not None

    # Load dataframe from disk and verify
    df_loaded = dataset_service.load_dataframe(ds1.id)
    assert len(df_loaded) == 2
    assert list(df_loaded.columns) == ["feature_x", "feature_y", "target"]

    # Reupload with different bytes -> produces a completely distinct dataset identity
    csv_bytes_v2 = b"feature_x,feature_y,target\n1.0,2.0,10.0\n3.0,4.0,99.0\n"
    ds2 = dataset_service.import_csv(
        project_id=project.id,
        raw_bytes=csv_bytes_v2,
        display_name="v2.csv",
    )

    assert ds2.id != ds1.id
    assert ds2.raw_sha256 != ds1.raw_sha256

    # Both datasets are independently listed
    all_ds = dataset_service.list_datasets(project.id)
    assert len(all_ds) == 2
    ids = {d.id for d in all_ds}
    assert ds1.id in ids and ds2.id in ids


def test_t07_demo_dataset_persistence(migrated_db: Path) -> None:
    """T07: Demo datasets persist and load without network."""
    project = ProjectService().create_project("Demo Project")
    dataset_service = DatasetService()

    iris_ds = dataset_service.load_demo(project.id, DemoDatasetKind.IRIS)
    assert iris_ds.source_kind == "demo"
    assert iris_ds.row_count == 150
    assert iris_ds.column_count == 5

    df = dataset_service.load_dataframe(iris_ds.id)
    assert len(df) == 150
    assert "species" in df.columns


def test_import_csv_invalid_project_rejection(migrated_db: Path) -> None:
    """Importing into a nonexistent project must fail with PROJECT_NOT_FOUND."""
    dataset_service = DatasetService()
    with pytest.raises(ServiceError) as exc_info:
        dataset_service.import_csv(
            project_id="nonexistent_id",
            raw_bytes=b"a,b\n1,2\n",
            display_name="test.csv",
        )
    assert exc_info.value.code == ErrorCode.PROJECT_NOT_FOUND
