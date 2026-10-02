"""SQLite repository implementations for projects and datasets."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from datamind.contracts import (
    DatasetSummary,
    ErrorCode,
    ProjectSummary,
    ServiceError,
)
from datamind.storage.database import get_connection


class ProjectRepository:
    """Repository for project persistence operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def create(self, name: str, description: str = "") -> ProjectSummary:
        """Create a new project."""
        # Check for duplicate active name
        conn = get_connection(self.db_path)
        try:
            existing = conn.execute(
                "SELECT id FROM projects WHERE name = ? AND archived_at IS NULL;",
                (name,),
            ).fetchone()
            if existing:
                raise ServiceError(
                    ErrorCode.PROJECT_ALREADY_EXISTS,
                    f"Project with name '{name}' already exists.",
                    field="name",
                )

            # Validate name is not empty/whitespace
            if not name or name.strip() == "":
                raise ServiceError(
                    ErrorCode.INVALID_TARGET,
                    "Project name cannot be empty or whitespace-only.",
                    field="name",
                )

            project_id = str(__import__("uuid").uuid4())
            created_at = datetime.now(timezone.utc).isoformat()

            conn.execute(
                """
                INSERT INTO projects (id, name, description, created_at)
                VALUES (?, ?, ?, ?);
                """,
                (project_id, name, description, created_at),
            )
            conn.commit()

            return ProjectSummary(
                id=project_id,
                name=name,
                description=description,
                created_at=created_at,
                archived_at=None,
            )
        finally:
            conn.close()

    def list_projects(self, include_archived: bool = False) -> List[ProjectSummary]:
        """List projects, optionally including archived ones."""
        conn = get_connection(self.db_path)
        try:
            if include_archived:
                rows = conn.execute(
                    "SELECT id, name, description, created_at, archived_at FROM projects ORDER BY created_at DESC;"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, name, description, created_at, archived_at FROM projects WHERE archived_at IS NULL ORDER BY created_at DESC;"
                ).fetchall()

            return [
                ProjectSummary(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    created_at=row["created_at"],
                    archived_at=row["archived_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()

    def get_by_id(self, project_id: str) -> Optional[ProjectSummary]:
        """Get a project by ID."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                "SELECT id, name, description, created_at, archived_at FROM projects WHERE id = ?;",
                (project_id,),
            ).fetchone()
            if row:
                return ProjectSummary(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    created_at=row["created_at"],
                    archived_at=row["archived_at"],
                )
            return None
        finally:
            conn.close()

    def archive(self, project_id: str) -> bool:
        """Soft-archive a project by setting archived_at."""
        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                "UPDATE projects SET archived_at = ? WHERE id = ? AND archived_at IS NULL;",
                (datetime.now(timezone.utc).isoformat(), project_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


class DatasetRepository:
    """Repository for dataset persistence operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def create(
        self,
        project_id: str,
        display_name: str,
        source_kind: str,
        source_json: str,
        raw_sha256: str,
        raw_relative_path: str,
        parser_version: str,
        parser_config_json: str,
        schema_json: str,
        profile_json: str,
        row_count: int,
        column_count: int,
    ) -> DatasetSummary:
        """Create a new dataset record."""
        # Validate project exists first
        conn = get_connection(self.db_path)
        try:
            project_row = conn.execute(
                "SELECT id FROM projects WHERE id = ?;",
                (project_id,),
            ).fetchone()
            if not project_row:
                raise ServiceError(
                    ErrorCode.PROJECT_NOT_FOUND,
                    f"Project with ID '{project_id}' not found.",
                    field="project_id",
                )
        finally:
            conn.close()

        dataset_id = str(__import__("uuid").uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        conn = get_connection(self.db_path)
        try:
            try:
                conn.execute(
                    """
                    INSERT INTO datasets (
                        id, project_id, display_name, source_kind, source_json,
                        raw_sha256, raw_relative_path, parser_version, parser_config_json,
                        schema_json, profile_json, row_count, column_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        dataset_id,
                        project_id,
                        display_name,
                        source_kind,
                        source_json,
                        raw_sha256,
                        raw_relative_path,
                        parser_version,
                        parser_config_json,
                        schema_json,
                        profile_json,
                        row_count,
                        column_count,
                        created_at,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                # Catches the DB-level UNIQUE(project_id, raw_sha256) violation as a
                # last-resort safety net against concurrent double-clicks that both
                # passed the pre-check simultaneously.
                # SQLite reports the error as either the index name or the column list
                # depending on platform/version — match on both.
                err_msg = str(exc)
                is_dup = "ux_datasets_project_sha256" in err_msg or (
                    "datasets.project_id" in err_msg and "datasets.raw_sha256" in err_msg
                )
                if is_dup:
                    raise ServiceError(
                        ErrorCode.DATASET_ALREADY_EXISTS,
                        "This dataset already exists in this project.",
                        details={"raw_sha256": raw_sha256},
                    ) from exc
                raise

            return DatasetSummary(
                id=dataset_id,
                project_id=project_id,
                display_name=display_name,
                source_kind=source_kind,
                source_json=source_json,
                raw_sha256=raw_sha256,
                raw_relative_path=raw_relative_path,
                parser_version=parser_version,
                parser_config_json=parser_config_json,
                schema_json=schema_json,
                profile_json=profile_json,
                row_count=row_count,
                column_count=column_count,
                created_at=created_at,
                archived_at=None,
            )
        finally:
            conn.close()

    def get_by_id(self, dataset_id: str) -> Optional[DatasetSummary]:
        """Get a dataset by ID."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT id, project_id, display_name, source_kind, source_json,
                       raw_sha256, raw_relative_path, parser_version, parser_config_json,
                       schema_json, profile_json, row_count, column_count, created_at, archived_at
                FROM datasets WHERE id = ?;
                """,
                (dataset_id,),
            ).fetchone()
            if row:
                return DatasetSummary(
                    id=row["id"],
                    project_id=row["project_id"],
                    display_name=row["display_name"],
                    source_kind=row["source_kind"],
                    source_json=row["source_json"],
                    raw_sha256=row["raw_sha256"],
                    raw_relative_path=row["raw_relative_path"],
                    parser_version=row["parser_version"],
                    parser_config_json=row["parser_config_json"],
                    schema_json=row["schema_json"],
                    profile_json=row["profile_json"],
                    row_count=row["row_count"],
                    column_count=row["column_count"],
                    created_at=row["created_at"],
                    archived_at=row["archived_at"],
                )
            return None
        finally:
            conn.close()

    def list_by_project(
        self, project_id: str, include_archived: bool = False
    ) -> List[DatasetSummary]:
        """List datasets for a project."""
        conn = get_connection(self.db_path)
        try:
            if include_archived:
                rows = conn.execute(
                    """
                    SELECT id, project_id, display_name, source_kind, source_json,
                           raw_sha256, raw_relative_path, parser_version, parser_config_json,
                           schema_json, profile_json, row_count, column_count, created_at, archived_at
                    FROM datasets WHERE project_id = ? ORDER BY created_at DESC;
                    """,
                    (project_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, project_id, display_name, source_kind, source_json,
                           raw_sha256, raw_relative_path, parser_version, parser_config_json,
                           schema_json, profile_json, row_count, column_count, created_at, archived_at
                    FROM datasets WHERE project_id = ? AND archived_at IS NULL ORDER BY created_at DESC;
                    """,
                    (project_id,),
                ).fetchall()

            return [
                DatasetSummary(
                    id=row["id"],
                    project_id=row["project_id"],
                    display_name=row["display_name"],
                    source_kind=row["source_kind"],
                    source_json=row["source_json"],
                    raw_sha256=row["raw_sha256"],
                    raw_relative_path=row["raw_relative_path"],
                    parser_version=row["parser_version"],
                    parser_config_json=row["parser_config_json"],
                    schema_json=row["schema_json"],
                    profile_json=row["profile_json"],
                    row_count=row["row_count"],
                    column_count=row["column_count"],
                    created_at=row["created_at"],
                    archived_at=row["archived_at"],
                )
                for row in rows
            ]
        finally:
            conn.close()

    def find_by_project_and_sha256(
        self, project_id: str, raw_sha256: str
    ) -> Optional[DatasetSummary]:
        """Return the active dataset matching this project and content hash, or None."""
        conn = get_connection(self.db_path)
        try:
            row = conn.execute(
                """
                SELECT id, project_id, display_name, source_kind, source_json,
                       raw_sha256, raw_relative_path, parser_version, parser_config_json,
                       schema_json, profile_json, row_count, column_count, created_at, archived_at
                FROM datasets
                WHERE project_id = ? AND raw_sha256 = ? AND archived_at IS NULL;
                """,
                (project_id, raw_sha256),
            ).fetchone()
            if row:
                return DatasetSummary(
                    id=row["id"],
                    project_id=row["project_id"],
                    display_name=row["display_name"],
                    source_kind=row["source_kind"],
                    source_json=row["source_json"],
                    raw_sha256=row["raw_sha256"],
                    raw_relative_path=row["raw_relative_path"],
                    parser_version=row["parser_version"],
                    parser_config_json=row["parser_config_json"],
                    schema_json=row["schema_json"],
                    profile_json=row["profile_json"],
                    row_count=row["row_count"],
                    column_count=row["column_count"],
                    created_at=row["created_at"],
                    archived_at=row["archived_at"],
                )
            return None
        finally:
            conn.close()

    def archive(self, dataset_id: str) -> bool:
        """Soft-archive a dataset by setting archived_at."""
        from datetime import datetime, timezone

        conn = get_connection(self.db_path)
        try:
            cursor = conn.execute(
                "UPDATE datasets SET archived_at = ? WHERE id = ? AND archived_at IS NULL;",
                (datetime.now(timezone.utc).isoformat(), dataset_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
