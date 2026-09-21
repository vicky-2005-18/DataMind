"""Shared pytest fixtures for DataMind test suite."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from datamind.config import Settings, reset_settings
from datamind.storage.database import run_migrations


@pytest.fixture
def tmp_storage_dir() -> Generator[Path, None, None]:
    """Provide an isolated temporary directory for test storage."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage_path = Path(tmp_dir) / "storage"
        logs_path = Path(tmp_dir) / "logs"
        settings = Settings(storage_dir=storage_path, logs_dir=logs_path)
        settings.ensure_directories()
        reset_settings(settings)
        yield storage_path
        reset_settings(None)


@pytest.fixture
def migrated_db(tmp_storage_dir: Path) -> Path:
    """Initialize a clean migrated SQLite database in isolated test storage."""
    db_path = tmp_storage_dir / "datamind.sqlite3"
    run_migrations(db_path)
    return db_path
