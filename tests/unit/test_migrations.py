"""Unit tests for SQLite migration runner idempotency and schema initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from datamind.storage.database import get_connection, run_migrations


def test_migration_idempotency(tmp_path: Path) -> None:
    """T01: Initializing DB twice applies migration once without errors."""
    db_path = tmp_path / "test_datamind.sqlite3"

    # First run applies migration 1
    applied_first = run_migrations(db_path)
    assert applied_first == [1]

    # Second run is an idempotent no-op
    applied_second = run_migrations(db_path)
    assert applied_second == []

    # Check migration tracking table
    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version, applied_at FROM schema_migrations;")
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0]["version"] == 1
        assert rows[0]["applied_at"] is not None

        # Check that core tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
        )
        tables = {row["name"] for row in cursor.fetchall()}
        expected_tables = {
            "schema_migrations",
            "projects",
            "datasets",
            "splits",
            "experiments",
            "trials",
            "artifacts",
            "model_selections",
            "evaluations",
            "metrics",
        }
        assert expected_tables.issubset(tables)
    finally:
        conn.close()


def test_foreign_keys_enforced(tmp_path: Path) -> None:
    """Verify that foreign keys are actively enforced on SQLite connections."""
    db_path = tmp_path / "fk_test.sqlite3"
    run_migrations(db_path)

    conn = get_connection(db_path)
    try:
        cursor = conn.cursor()
        # Attempting to insert a dataset referencing a nonexistent project should fail
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute(
                """
                INSERT INTO datasets (
                    id, project_id, display_name, source_kind, source_json,
                    raw_sha256, raw_relative_path, parser_version, parser_config_json,
                    schema_json, profile_json, row_count, column_count, created_at
                ) VALUES (
                    'ds_1', 'nonexistent_project_id', 'demo.csv', 'upload', '{}',
                    'fakehash', 'datasets/ds_1/raw.csv', '1.0', '{}',
                    '{}', '{}', 10, 2, '2026-09-21T00:00:00Z'
                );
                """
            )
    finally:
        conn.close()
