"""Structural profiling and quality inspection for tabular datasets."""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd

from datamind.contracts import (
    ColumnProfile,
    ColumnRole,
    ColumnSchema,
    DatasetProfile,
    TableSchema,
)


def profile_dataframe(df: pd.DataFrame) -> Tuple[DatasetProfile, TableSchema]:
    """Compute comprehensive structural profile, quality warnings, and role suggestions."""
    row_count = len(df)
    column_count = len(df.columns)
    duplicate_row_count = int(df.duplicated().sum())
    memory_bytes = int(df.memory_usage(deep=True).sum())

    column_profiles: List[ColumnProfile] = []
    column_schemas: List[ColumnSchema] = []
    overall_warnings: List[str] = []

    if duplicate_row_count > 0:
        overall_warnings.append(
            f"Dataset contains {duplicate_row_count:,} duplicate rows ({duplicate_row_count / row_count:.1%})."
        )

    for col in df.columns:
        series = df[col]
        non_null_count = int(series.count())
        null_count = row_count - non_null_count
        null_percentage = (null_count / row_count * 100.0) if row_count > 0 else 0.0
        unique_count = int(series.nunique(dropna=True))

        is_numeric = pd.api.types.is_numeric_dtype(series)
        is_constant = unique_count <= 1
        is_all_null = non_null_count == 0

        # Sample values
        sample_non_nulls = series.dropna().unique()[:5]
        sample_str = [str(val) for val in sample_non_nulls]

        col_warnings: List[str] = []

        if is_all_null:
            col_warnings.append("Column is completely empty (100% missing).")
            suggested_role = ColumnRole.CONSTANT
        elif is_constant:
            col_warnings.append("Column has only 1 distinct value (constant).")
            suggested_role = ColumnRole.CONSTANT
        elif not is_numeric and unique_count > 50:
            col_warnings.append(
                f"High cardinality: {unique_count} distinct categories exceeds the 50-category limit."
            )
            suggested_role = ColumnRole.UNSUPPORTED
        elif unique_count == row_count and row_count >= 20:
            col_warnings.append("Values are 100% unique across all rows (likely an ID or key column).")
            suggested_role = ColumnRole.ID_LIKE
        elif is_numeric:
            suggested_role = ColumnRole.NUMERIC
        else:
            suggested_role = ColumnRole.CATEGORICAL

        if null_percentage > 50.0 and not is_all_null:
            col_warnings.append(f"High missingness: {null_percentage:.1f}% missing values.")

        dtype_str = str(series.dtype)

        profile = ColumnProfile(
            name=col,
            dtype=dtype_str,
            suggested_role=suggested_role,
            total_count=row_count,
            non_null_count=non_null_count,
            null_count=null_count,
            null_percentage=round(null_percentage, 2),
            unique_count=unique_count,
            is_constant=is_constant,
            sample_values=sample_str,
            warnings=col_warnings,
        )
        column_profiles.append(profile)

        column_schemas.append(
            ColumnSchema(
                name=col,
                inferred_type=dtype_str,
                suggested_role=suggested_role,
            )
        )

        for w in col_warnings:
            overall_warnings.append(f"Column '{col}': {w}")

    dataset_profile = DatasetProfile(
        row_count=row_count,
        column_count=column_count,
        duplicate_row_count=duplicate_row_count,
        memory_bytes=memory_bytes,
        columns=column_profiles,
        quality_warnings=overall_warnings,
    )

    table_schema = TableSchema(
        columns=column_schemas,
        column_names=list(df.columns),
    )

    return dataset_profile, table_schema
