"""Tests for storage/artifacts.py module."""

from pathlib import Path

import pytest

from datamind.storage.artifacts import (
    compute_sha256_file,
    safe_relative_path,
    write_atomic_bytes,
)


def test_compute_sha256_file(tmp_path: Path) -> None:
    """Test SHA-256 file hashing."""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    # Compute the actual hash for "test content"
    expected_hash = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"

    result = compute_sha256_file(test_file)
    assert result == expected_hash


def test_compute_sha256_file_empty(tmp_path: Path) -> None:
    """Test SHA-256 hashing of empty file."""
    test_file = tmp_path / "empty.txt"
    test_file.write_text("")

    # Known SHA-256 for empty string
    expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    result = compute_sha256_file(test_file)
    assert result == expected_hash


def test_safe_relative_path_valid(tmp_path: Path) -> None:
    """Test safe_relative_path with valid relative paths."""
    base = tmp_path / "storage"
    base.mkdir()

    # The function expects target to be an absolute path within base
    # and returns the relative path from base to target as a string
    target1 = base / "datasets" / "file.csv"
    result1 = safe_relative_path(base, target1)
    assert ".." not in result1
    assert "datasets" in result1 and "file.csv" in result1

    target2 = base / "experiments" / "exp" / "config.json"
    result2 = safe_relative_path(base, target2)
    assert ".." not in result2
    assert "experiments" in result2 and "config.json" in result2

    target3 = base / "a" / "b" / "c" / "d" / "file.txt"
    result3 = safe_relative_path(base, target3)
    assert ".." not in result3
    assert "a" in result3 and "file.txt" in result3


def test_safe_relative_path_traversal_rejected(tmp_path: Path) -> None:
    """Test safe_relative_path rejects path traversal attempts."""
    base = tmp_path / "storage"
    base.mkdir()

    # Target outside base should raise ValueError
    outside = tmp_path / "outside.txt"
    with pytest.raises(ValueError):
        safe_relative_path(base, outside)

    # Target with parent references should raise ValueError
    with pytest.raises(ValueError):
        safe_relative_path(base, base / "datasets" / ".." / "etc" / "passwd")


def test_safe_relative_path_absolute_rejected(tmp_path: Path) -> None:
    """Test safe_relative_path rejects absolute paths outside base."""
    base = tmp_path / "storage"
    base.mkdir()

    # Absolute paths outside base should raise ValueError
    outside_abs = tmp_path / "etc" / "passwd"
    with pytest.raises(ValueError):
        safe_relative_path(base, outside_abs)


def test_write_atomic_bytes(tmp_path: Path) -> None:
    """Test atomic write behavior."""
    target = tmp_path / "output.txt"
    content = b"test content"

    # Write atomically
    write_atomic_bytes(target, content)

    # File should exist with correct content
    assert target.exists()
    assert target.read_bytes() == content


def test_write_atomic_bytes_creates_parent(tmp_path: Path) -> None:
    """Test atomic write creates parent directories."""
    target = tmp_path / "subdir" / "nested" / "output.txt"
    content = b"test content"

    # Write atomically to nested path
    write_atomic_bytes(target, content)

    # File should exist with correct content
    assert target.exists()
    assert target.read_bytes() == content


def test_write_atomic_bytes_overwrites(tmp_path: Path) -> None:
    """Test atomic write overwrites existing file."""
    target = tmp_path / "output.txt"
    target.write_bytes(b"old content")

    new_content = b"new content"
    write_atomic_bytes(target, new_content)

    # File should have new content
    assert target.read_bytes() == new_content
