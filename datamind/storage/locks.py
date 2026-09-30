"""Workspace lock for single-flight training/finalization operations."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock


class WorkspaceLock:
    """File-based lock ensuring single-flight training/finalization operations."""

    def __init__(self, lock_file: Path):
        self.lock_file = lock_file
        self._lock = FileLock(lock_file, timeout=60)

    @property
    def is_locked(self) -> bool:
        """Check if the lock is currently held."""
        return self._lock.is_locked

    @contextmanager
    def acquire(self):
        """Acquire the lock as a context manager."""
        with self._lock:
            yield
