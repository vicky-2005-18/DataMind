"""Integration tests for project persistence across service reloads."""

from __future__ import annotations

from pathlib import Path

import pytest

from datamind.contracts import ErrorCode, ServiceError
from datamind.services.projects import ProjectService
from datamind.storage.repositories import ProjectRepository


def test_project_create_and_reopen_persistence(migrated_db: Path) -> None:
    """T01: Create project, simulate restart by reopening with fresh repo, verify persistence."""
    repo1 = ProjectRepository(migrated_db)
    service1 = ProjectService(repo1)

    project = service1.create_project(
        name="Iris Classification Research",
        description="First exploratory project",
    )
    assert project.id is not None
    assert project.name == "Iris Classification Research"
    assert project.description == "First exploratory project"
    assert project.archived_at is None

    # Simulate app restart with a fresh service and fresh repository instance
    repo2 = ProjectRepository(migrated_db)
    service2 = ProjectService(repo2)

    retrieved = service2.get_project(project.id)
    assert retrieved is not None
    assert retrieved.id == project.id
    assert retrieved.name == "Iris Classification Research"
    assert retrieved.description == "First exploratory project"
    assert retrieved.created_at == project.created_at

    # Listing projects shows the created project
    projects = service2.list_projects()
    assert len(projects) == 1
    assert projects[0].id == project.id


def test_project_duplicate_name_rejection(migrated_db: Path) -> None:
    """Attempting to create another active project with the exact same name must raise ServiceError."""
    service = ProjectService(ProjectRepository(migrated_db))
    service.create_project("Unique Project")

    with pytest.raises(ServiceError) as exc_info:
        service.create_project("Unique Project")
    assert exc_info.value.code == ErrorCode.PROJECT_ALREADY_EXISTS


def test_project_empty_name_rejection(migrated_db: Path) -> None:
    """Empty or whitespace-only project name must be rejected."""
    service = ProjectService(ProjectRepository(migrated_db))
    with pytest.raises(ServiceError) as exc_info:
        service.create_project("   ")
    assert exc_info.value.code == ErrorCode.INVALID_TARGET


def test_project_soft_archive(migrated_db: Path) -> None:
    """Archiving a project sets archived_at and excludes it from standard list."""
    service = ProjectService(ProjectRepository(migrated_db))
    p1 = service.create_project("Project 1")
    p2 = service.create_project("Project 2")

    active_list = service.list_projects(include_archived=False)
    assert len(active_list) == 2

    # Archive p1
    archived = service.archive_project(p1.id)
    assert archived is True

    # Active list now contains only p2
    active_after = service.list_projects(include_archived=False)
    assert len(active_after) == 1
    assert active_after[0].id == p2.id

    # Full list still includes p1
    all_projects = service.list_projects(include_archived=True)
    assert len(all_projects) == 2
    archived_p1 = next(p for p in all_projects if p.id == p1.id)
    assert archived_p1.archived_at is not None
