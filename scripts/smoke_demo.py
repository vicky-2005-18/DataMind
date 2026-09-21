"""Service-level smoke demo verifying projects (M0) and datasets (M1)."""

from __future__ import annotations

import sys
import uuid

from datamind.config import get_settings
from datamind.contracts import DemoDatasetKind
from datamind.services.datasets import DatasetService
from datamind.services.projects import ProjectService
from datamind.storage.database import run_migrations


def run_smoke_demo() -> int:
    print("=" * 60)
    print("DataMind M0/M1 Smoke Demo: Projects & Datasets")
    print("=" * 60)

    settings = get_settings()
    settings.ensure_directories()
    applied = run_migrations(settings.db_path)
    print(f"Applied migrations: {applied}")

    project_service = ProjectService()
    dataset_service = DatasetService()

    # 1. Create project
    demo_name = f"Smoke Demo Project {uuid.uuid4().hex[:6]}"
    print(f"\n1. Creating project: '{demo_name}'")
    project = project_service.create_project(
        name=demo_name,
        description="Demo project created during smoke verification",
    )
    print(f"   -> Project ID: {project.id}")

    # 2. Reopen project from persistent storage
    print("\n2. Verifying project persistence...")
    retrieved = ProjectService().get_project(project.id)
    if not retrieved or retrieved.name != demo_name:
        print("[-] Project persistence verification failed.")
        return 1
    print(f"   -> Verified project: '{retrieved.name}'")

    # 3. Ingest Iris demo dataset
    print("\n3. Ingesting Iris offline demo dataset (M1)...")
    iris_ds = dataset_service.load_demo(project.id, DemoDatasetKind.IRIS)
    print(f"   -> Dataset ID: {iris_ds.id}")
    print(f"   -> Display Name: {iris_ds.display_name}")
    print(f"   -> Dimensions: {iris_ds.row_count:,} rows, {iris_ds.column_count} columns")
    print(f"   -> Raw SHA-256: {iris_ds.raw_sha256}")
    print(f"   -> Relative Storage Path: {iris_ds.raw_relative_path}")

    # 4. Verify structural profile
    profile = iris_ds.get_profile()
    print("\n4. Structural Profile:")
    print(f"   -> Duplicate rows: {profile.duplicate_row_count}")
    print(f"   -> Memory size: {profile.memory_bytes} bytes")
    for col in profile.columns:
        print(f"      - {col.name:15} | {col.dtype:10} | Role: {col.suggested_role.value:12} | Nulls: {col.null_count}")

    # 5. Load raw dataframe from storage with hash verification
    print("\n5. Verifying raw file hash and loading dataframe...")
    df = dataset_service.load_dataframe(iris_ds.id)
    print(f"   -> Successfully verified and loaded {len(df)} rows from immutable storage.")
    print(f"   -> Columns: {list(df.columns)}")

    print("\nAll M0/M1 Smoke Demo checks completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(run_smoke_demo())
