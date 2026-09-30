"""Tests for storage/experiment_repos.py module."""

from pathlib import Path
import pytest

from datamind.storage.database import get_connection
from datamind.storage.experiment_repos import SplitRepository
from datamind.storage.repositories import DatasetRepository, ProjectRepository


def test_split_repository_missing_manifest_raises_error(migrated_db: Path) -> None:
    """Test SplitRepository raises FileNotFoundError when manifest file is missing."""
    storage_dir = migrated_db.parent
    storage_dir.mkdir(exist_ok=True)

    # Create project and dataset first for foreign key constraint
    project_repo = ProjectRepository(migrated_db)
    dataset_repo = DatasetRepository(migrated_db)
    project = project_repo.create(name="Test", description="Test")
    dataset = dataset_repo.create(
        project_id=project.id,
        display_name="test.csv",
        source_kind="upload",
        source_json='{"byte_size": 100}',
        raw_sha256="abc123",
        raw_relative_path="datasets/test/raw.csv",
        parser_version="1.0",
        parser_config_json='{"delimiter": ","}',
        schema_json='{"columns": []}',
        profile_json='{"row_count": 10}',
        row_count=10,
        column_count=2,
    )

    repo = SplitRepository(migrated_db)

    # Create a split record pointing to a non-existent manifest
    split_id = "test-split-id"
    conn = get_connection(migrated_db)
    try:
        conn.execute(
            """
            INSERT INTO splits (
                id, dataset_id, task, target, view_fingerprint, split_fingerprint,
                config_json, row_policy_json, manifest_relative_path, manifest_sha256, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                split_id,
                dataset.id,  # Use actual dataset_id for foreign key
                "classification",
                "species",
                "fingerprint123",
                "splitfingerprint456",
                '{"test_fraction": 0.2}',
                '{"test": "policy"}',
                "splits/test/manifest.json",  # Non-existent file
                "hash123",
                "2024-01-01T00:00:00Z",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # Attempting to get the split should raise FileNotFoundError
    with pytest.raises(FileNotFoundError, match="Split manifest file not found"):
        repo.get_by_id(split_id)
