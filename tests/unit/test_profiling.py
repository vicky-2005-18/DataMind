"""Unit tests for dataset profiling and role suggestion rules."""

from __future__ import annotations

import pandas as pd

from datamind.contracts import ColumnRole
from datamind.data.profiling import profile_dataframe


def test_profiling_roles_and_warnings() -> None:
    # Build dataframe with various column characteristics
    data = {
        "id_col": [f"user_{i}" for i in range(30)],
        "num_col": [float(i) for i in range(30)],
        "cat_col": ["A", "B", "C"] * 10,
        "constant_col": [42] * 30,
        "high_card_cat": [f"category_{i}" for i in range(30)] * 1,  # 30 unique
    }
    # Append 30 more rows for high_card_cat to exceed 50 unique
    data["high_card_cat"] = [f"cat_{i}" for i in range(60)]
    data["id_col"] = [f"user_{i}" for i in range(60)]
    data["num_col"] = [float(i) for i in range(60)]
    data["cat_col"] = ["A", "B", "C"] * 20
    data["constant_col"] = [42] * 60

    # Add duplicate rows
    df = pd.DataFrame(data)
    df = pd.concat([df, df.iloc[:5]], ignore_index=True)

    profile, schema = profile_dataframe(df)

    assert profile.row_count == 65
    assert profile.column_count == 5
    assert profile.duplicate_row_count == 5

    col_map = {c.name: c for c in profile.columns}

    # Constant column check
    assert col_map["constant_col"].is_constant is True
    assert col_map["constant_col"].suggested_role == ColumnRole.CONSTANT

    # ID-like column check (unique values match row count)
    assert col_map["num_col"].suggested_role == ColumnRole.NUMERIC

    # High cardinality check (>50 unique categories)
    assert col_map["high_card_cat"].suggested_role == ColumnRole.UNSUPPORTED
    assert any("50-category limit" in w for w in col_map["high_card_cat"].warnings)
