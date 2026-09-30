"""Tests for storage/repositories.py module."""

from pathlib import Path
import pytest

from datamind.contracts import ErrorCode, ServiceError
from datamind.storage.repositories import ProjectRepository, DatasetRepository


def test_project_repository_create_and_get(migrated_db: Path) -> None:
    """Test ProjectRepository create and get operations."""
    repo = ProjectRepository(migrated_db)
    
    # Create a project
    project = repo.create(
        name="Test Project",
        description="Test description",
    )
    
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "Test description"
    
    # Get by ID
    retrieved = repo.get_by_id(project.id)
    assert retrieved is not None
    assert retrieved.id == project.id
    assert retrieved.name == "Test Project"


def test_dataset_repository_create_validates_project(migrated_db: Path) -> None:
    """Test DatasetRepository validates project existence."""
    project_repo = ProjectRepository(migrated_db)
    dataset_repo = DatasetRepository(migrated_db)
    
    # Create a project first
    project = project_repo.create(name="Test Project", description="Test")
    
    # Create dataset with valid project should succeed
    dataset = dataset_repo.create(
        project_id=project.id,
        display_name="test.csv",
        source_kind="upload",
        source_json='{"byte_size": 100, "kind": "upload"}',
        raw_sha256="abc123",
        raw_relative_path="datasets/test/raw.csv",
        parser_version="1.0",
        parser_config_json='{"delimiter": ","}',
        schema_json='{"columns": []}',
        profile_json='{"row_count": 10}',
        row_count=10,
        column_count=2,
    )
    
    assert dataset.id is not None
    assert dataset.project_id == project.id


def test_dataset_repository_invalid_project_raises_error(migrated_db: Path) -> None:
    """Test DatasetRepository raises ServiceError for nonexistent project."""
    dataset_repo = DatasetRepository(migrated_db)
    
    # Creating dataset with nonexistent project should raise ServiceError
    with pytest.raises(ServiceError) as exc_info:
        dataset_repo.create(
            project_id="nonexistent_id",
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
    
    assert exc_info.value.code == ErrorCode.PROJECT_NOT_FOUND
