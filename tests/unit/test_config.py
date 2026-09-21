"""Unit tests for configuration and path resolution."""

from __future__ import annotations

from pathlib import Path

from datamind.config import Settings


def test_settings_default_paths(tmp_path: Path) -> None:
    settings = Settings(storage_dir=tmp_path / "custom_storage")
    assert settings.storage_dir == tmp_path / "custom_storage"
    assert settings.db_path == tmp_path / "custom_storage" / "datamind.sqlite3"
    assert settings.datasets_dir == tmp_path / "custom_storage" / "datasets"
    assert settings.max_upload_bytes == settings.max_upload_mib * 1024 * 1024


def test_ensure_directories(tmp_path: Path) -> None:
    settings = Settings(storage_dir=tmp_path / "store", logs_dir=tmp_path / "logs")
    settings.ensure_directories()
    assert (tmp_path / "store").is_dir()
    assert (tmp_path / "store" / "datasets").is_dir()
    assert (tmp_path / "store" / "splits").is_dir()
    assert (tmp_path / "store" / "experiments").is_dir()
    assert (tmp_path / "store" / "exports").is_dir()
    assert (tmp_path / "store" / "tmp").is_dir()
    assert (tmp_path / "logs").is_dir()
