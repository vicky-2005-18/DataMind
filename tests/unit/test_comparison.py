"""Tests for services/comparison.py module."""

from pathlib import Path

import pytest

from datamind.contracts import ErrorCode, ServiceError
from datamind.services.comparison import ComparisonService


def test_comparison_service_raises_on_empty_list(migrated_db: Path) -> None:
    """Test ComparisonService raises error when given empty experiment list."""
    comparison = ComparisonService(migrated_db)

    with pytest.raises(ServiceError) as exc_info:
        comparison.compare([])

    assert exc_info.value.code == ErrorCode.INCOMPATIBLE_COMPARISON


def test_comparison_service_raises_on_single_experiment(migrated_db: Path) -> None:
    """Test ComparisonService raises error when given only one experiment."""
    comparison = ComparisonService(migrated_db)

    with pytest.raises(ServiceError) as exc_info:
        comparison.compare(["exp1"])

    assert exc_info.value.code == ErrorCode.INCOMPATIBLE_COMPARISON
