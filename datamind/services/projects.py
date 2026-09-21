"""Project orchestration service."""

from __future__ import annotations

from typing import List, Optional

from datamind.config import get_settings
from datamind.contracts import ProjectSummary
from datamind.storage.repositories import ProjectRepository


class ProjectService:
    """Service handling project creation, listing, retrieval, and archiving."""

    def __init__(self, repo: Optional[ProjectRepository] = None):
        if repo is None:
            settings = get_settings()
            repo = ProjectRepository(settings.db_path)
        self.repo = repo

    def create_project(self, name: str, description: str = "") -> ProjectSummary:
        """Create a new project and return its summary."""
        return self.repo.create(name=name, description=description)

    def list_projects(self, include_archived: bool = False) -> List[ProjectSummary]:
        """List active or all projects."""
        return self.repo.list_projects(include_archived=include_archived)

    def get_project(self, project_id: str) -> Optional[ProjectSummary]:
        """Get project by ID."""
        return self.repo.get_by_id(project_id)

    def archive_project(self, project_id: str) -> bool:
        """Soft-archive project by ID."""
        return self.repo.archive(project_id)
