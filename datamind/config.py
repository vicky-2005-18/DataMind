"""Typed configuration, resource limits, and path management for DataMind."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env if present
load_dotenv()


class Settings(BaseModel):
    """Application configuration settings with validation."""

    storage_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("DATAMIND_STORAGE_DIR", "./storage")).resolve()
    )
    logs_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("DATAMIND_LOGS_DIR", "./logs")).resolve()
    )
    log_level: str = Field(default_factory=lambda: os.getenv("DATAMIND_LOG_LEVEL", "INFO"))
    max_upload_mib: int = Field(
        default_factory=lambda: int(os.getenv("DATAMIND_MAX_UPLOAD_MIB", "10"))
    )
    max_rows: int = Field(default_factory=lambda: int(os.getenv("DATAMIND_MAX_ROWS", "20000")))
    max_columns: int = Field(
        default_factory=lambda: int(os.getenv("DATAMIND_MAX_COLUMNS", "100"))
    )
    default_seed: int = Field(
        default_factory=lambda: int(os.getenv("DATAMIND_DEFAULT_SEED", "42"))
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mib * 1024 * 1024

    @property
    def db_path(self) -> Path:
        return self.storage_dir / "datamind.sqlite3"

    @property
    def datasets_dir(self) -> Path:
        return self.storage_dir / "datasets"

    @property
    def splits_dir(self) -> Path:
        return self.storage_dir / "splits"

    @property
    def experiments_dir(self) -> Path:
        return self.storage_dir / "experiments"

    @property
    def exports_dir(self) -> Path:
        return self.storage_dir / "exports"

    @property
    def tmp_dir(self) -> Path:
        return self.storage_dir / "tmp"

    @property
    def lock_path(self) -> Path:
        return self.storage_dir / ".workspace.lock"

    @property
    def locks_dir(self) -> Path:
        return self.storage_dir / "locks"

    @property
    def storage_root(self) -> Path:
        """Alias for storage_dir for backward-compat with recovery service."""
        return self.storage_dir

    def ensure_directories(self) -> None:
        """Create all required local storage and log directories."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.splits_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.locks_dir.mkdir(parents=True, exist_ok=True)


# Global settings singleton accessor
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Return the global Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings(new_settings: Optional[Settings] = None) -> None:
    """Reset the global settings instance (primarily for tests)."""
    global _settings
    _settings = new_settings
