"""Artifact file operations: hashing, path safety, and atomic writes."""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_sha256_file(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def safe_relative_path(base: Path, target: Path) -> str:
    """
    Compute a relative path from base to target, rejecting path traversal.
    Raises ValueError if target is not within base or uses parent references.
    """
    try:
        rel_path = target.relative_to(base)
        # Check for parent directory references
        if ".." in str(rel_path):
            raise ValueError("Path traversal detected")
        return str(rel_path)
    except ValueError as e:
        raise ValueError(f"Target path is not within base: {e}")


def write_atomic_bytes(file_path: Path, content: bytes) -> str:
    """
    Write bytes to a file atomically using temp file + rename.
    Returns the SHA-256 hash of the written content.
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temporary file
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
    with temp_path.open("wb") as f:
        f.write(content)
        f.flush()

    # Compute hash
    sha256_hash = hashlib.sha256(content).hexdigest()

    # Atomic rename
    temp_path.replace(file_path)

    return sha256_hash
