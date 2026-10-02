"""Tests for dataset duplicate detection (requirement: SHA-256 content-based, project-scoped).

Coverage:
  T-DUP-01  Same file same project => rejected, count stays at 1.
  T-DUP-02  Renamed file same content same project => rejected (hash-based, not filename).
  T-DUP-03  Different content same project => accepted, count becomes 2.
  T-DUP-04  Same content different project => accepted (project-scoped).
  T-DUP-05  Rejected upload leaves no DB record (count invariant after refresh).
  T-DUP-06  find_by_project_and_sha256 returns None for unknown hash.
  T-DUP-07  DB UNIQUE index rejects concurrent race-condition duplicate via IntegrityError.
  T-DUP-08  Migration 002 applied => ux_datasets_project_sha256 index exists.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from datamind.contracts import ErrorCode, ServiceError
from datamind.storage.database import get_connection
from datamind.storage.repositories import DatasetRepository, ProjectRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HEADER = "a,b,c\n"
_ROW_A = "1,2,3\n"
_ROW_B = "4,5,6\n"

CSV_CONTENT_A: bytes = (_HEADER + _ROW_A).encode()
CSV_CONTENT_B: bytes = (_HEADER + _ROW_B).encode()

SHA_A = hashlib.sha256(CSV_CONTENT_A).hexdigest()
SHA_B = hashlib.sha256(CSV_CONTENT_B).hexdigest()

_COMMON_FIELDS = dict(
    source_kind="upload",
    source_json='{"kind": "upload"}',
    parser_version="1.0",
    parser_config_json='{"delimiter": ","}',
    schema_json='{"columns": []}',
    profile_json='{"row_count": 1}',
    row_count=1,
    column_count=3,
)


def _insert(
    repo: DatasetRepository,
    project_id: str,
    sha: str,
    rel_path: str,
    name: str = "test.csv",
):
    return repo.create(
        project_id=project_id,
        display_name=name,
        raw_sha256=sha,
        raw_relative_path=rel_path,
        **_COMMON_FIELDS,
    )


# ---------------------------------------------------------------------------
# T-DUP-08  Migration 002 index exists
# ---------------------------------------------------------------------------


def test_migration_002_index_exists(migrated_db: Path) -> None:
    """T-DUP-08: ux_datasets_project_sha256 unique index is present after migrations."""
    conn = get_connection(migrated_db)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='ux_datasets_project_sha256';"
        ).fetchone()
        assert row is not None, "UNIQUE index ux_datasets_project_sha256 not found"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# T-DUP-06  find_by_project_and_sha256 returns None for unknown hash
# ---------------------------------------------------------------------------


def test_find_by_project_and_sha256_miss(migrated_db: Path) -> None:
    """T-DUP-06: lookup returns None when no dataset matches the hash."""
    proj = ProjectRepository(migrated_db).create("proj-miss")
    repo = DatasetRepository(migrated_db)
    result = repo.find_by_project_and_sha256(proj.id, "deadbeef" * 8)
    assert result is None


# ---------------------------------------------------------------------------
# T-DUP-01  Same file same project => rejected
# ---------------------------------------------------------------------------


def test_duplicate_same_file_rejected(migrated_db: Path) -> None:
    """T-DUP-01: Uploading the same content twice raises DATASET_ALREADY_EXISTS."""
    proj = ProjectRepository(migrated_db).create("proj-dup01")
    repo = DatasetRepository(migrated_db)

    _insert(repo, proj.id, SHA_A, "datasets/ds1/raw.csv", "file.csv")

    with pytest.raises(ServiceError) as exc_info:
        _insert(repo, proj.id, SHA_A, "datasets/ds2/raw.csv", "file.csv")

    assert exc_info.value.code == ErrorCode.DATASET_ALREADY_EXISTS


# ---------------------------------------------------------------------------
# T-DUP-02  Renamed file same content => rejected
# ---------------------------------------------------------------------------


def test_duplicate_renamed_file_rejected(migrated_db: Path) -> None:
    """T-DUP-02: Renaming a file does not bypass hash-based duplicate detection."""
    proj = ProjectRepository(migrated_db).create("proj-dup02")
    repo = DatasetRepository(migrated_db)

    _insert(repo, proj.id, SHA_A, "datasets/ds1/raw.csv", "original_name.csv")

    with pytest.raises(ServiceError) as exc_info:
        _insert(repo, proj.id, SHA_A, "datasets/ds2/raw.csv", "renamed_copy.csv")

    assert exc_info.value.code == ErrorCode.DATASET_ALREADY_EXISTS


# ---------------------------------------------------------------------------
# T-DUP-03  Different content same project => accepted, count = 2
# ---------------------------------------------------------------------------


def test_different_content_accepted(migrated_db: Path) -> None:
    """T-DUP-03: Two uploads with different content are both stored; count = 2."""
    proj = ProjectRepository(migrated_db).create("proj-dup03")
    repo = DatasetRepository(migrated_db)

    _insert(repo, proj.id, SHA_A, "datasets/ds1/raw.csv", "file_a.csv")
    _insert(repo, proj.id, SHA_B, "datasets/ds2/raw.csv", "file_b.csv")

    datasets = repo.list_by_project(proj.id)
    assert len(datasets) == 2


# ---------------------------------------------------------------------------
# T-DUP-04  Same content different project => accepted
# ---------------------------------------------------------------------------


def test_same_content_different_project_accepted(migrated_db: Path) -> None:
    """T-DUP-04: Duplicate detection is project-scoped; same hash in another project is OK."""
    proj_repo = ProjectRepository(migrated_db)
    proj_a = proj_repo.create("proj-dup04a")
    proj_b = proj_repo.create("proj-dup04b")
    repo = DatasetRepository(migrated_db)

    _insert(repo, proj_a.id, SHA_A, "datasets/ds1/raw.csv")
    _insert(repo, proj_b.id, SHA_A, "datasets/ds2/raw.csv")

    assert len(repo.list_by_project(proj_a.id)) == 1
    assert len(repo.list_by_project(proj_b.id)) == 1


# ---------------------------------------------------------------------------
# T-DUP-05  Rejected duplicate leaves no DB record (count invariant)
# ---------------------------------------------------------------------------


def test_rejected_duplicate_no_db_record(migrated_db: Path) -> None:
    """T-DUP-05: After a rejected duplicate attempt the dataset count remains unchanged."""
    proj = ProjectRepository(migrated_db).create("proj-dup05")
    repo = DatasetRepository(migrated_db)

    _insert(repo, proj.id, SHA_A, "datasets/ds1/raw.csv")
    assert len(repo.list_by_project(proj.id)) == 1

    with pytest.raises(ServiceError):
        _insert(repo, proj.id, SHA_A, "datasets/ds2/raw.csv")

    assert len(repo.list_by_project(proj.id)) == 1


# ---------------------------------------------------------------------------
# T-DUP-07  DB-level UNIQUE violation maps to DATASET_ALREADY_EXISTS
# ---------------------------------------------------------------------------


def test_db_unique_constraint_maps_to_service_error(migrated_db: Path) -> None:
    """T-DUP-07: A raw IntegrityError from the unique index maps to DATASET_ALREADY_EXISTS."""
    proj = ProjectRepository(migrated_db).create("proj-dup07")
    repo = DatasetRepository(migrated_db)

    _insert(repo, proj.id, SHA_A, "datasets/ds1/raw.csv")

    original_find = repo.find_by_project_and_sha256
    repo.find_by_project_and_sha256 = lambda *_: None  # type: ignore[method-assign]
    try:
        with pytest.raises(ServiceError) as exc_info:
            _insert(repo, proj.id, SHA_A, "datasets/ds99/raw.csv")
        assert exc_info.value.code == ErrorCode.DATASET_ALREADY_EXISTS
    finally:
        repo.find_by_project_and_sha256 = original_find  # type: ignore[method-assign]

def test_delete_dataset_archives_record(migrated_db):
    proj = ProjectRepository(migrated_db).create('proj-del01')
    repo = DatasetRepository(migrated_db)
    ds = _insert(repo, proj.id, SHA_A, 'datasets/ds1/raw.csv')
    assert len(repo.list_by_project(proj.id)) == 1
    assert repo.archive(ds.id) is True
    assert len(repo.list_by_project(proj.id)) == 0
    all_ds = repo.list_by_project(proj.id, include_archived=True)
    assert len(all_ds) == 1
    assert all_ds[0].archived_at is not None
