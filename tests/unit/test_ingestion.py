"""Unit tests for CSV ingestion contracts (T02, T03, T04, T05)."""

from __future__ import annotations

import io

import pandas as pd
import pytest

from datamind.contracts import ErrorCode, ServiceError
from datamind.data.ingestion import validate_and_parse_csv


def test_t02_utf8_and_utf8_bom_equivalence() -> None:
    """T02: Standard UTF-8 and UTF-8-BOM produce identical clean headers and values."""
    csv_text = "col_a,col_b,col_c\n1,apple,3.14\n2,banana,2.71\n"
    utf8_bytes = csv_text.encode("utf-8")
    bom_bytes = b"\xef\xbb\xbf" + utf8_bytes

    parsed_utf8 = validate_and_parse_csv(utf8_bytes, filename="utf8.csv")
    parsed_bom = validate_and_parse_csv(bom_bytes, filename="bom.csv")

    assert list(parsed_utf8.df.columns) == ["col_a", "col_b", "col_c"]
    assert list(parsed_bom.df.columns) == ["col_a", "col_b", "col_c"]
    assert parsed_utf8.df.equals(parsed_bom.df)
    assert parsed_bom.parser_config["encoding"] == "utf-8-sig"


def test_t03_empty_and_header_only_rejected() -> None:
    """T03: Empty files and header-only CSVs must raise INVALID_CSV."""
    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(b"", filename="empty.csv")
    assert exc_info.value.code == ErrorCode.INVALID_CSV

    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(b"   \n\n", filename="blank.csv")
    assert exc_info.value.code == ErrorCode.INVALID_CSV

    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(b"feature1,feature2,feature3\n", filename="header_only.csv")
    assert exc_info.value.code == ErrorCode.INVALID_CSV


def test_t03_duplicate_and_empty_headers_rejected() -> None:
    """T03: Duplicate column headers after trimming or empty headers must be rejected."""
    # Duplicate headers
    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(b"age,salary,age\n25,50000,25\n")
    assert exc_info.value.code == ErrorCode.INVALID_CSV
    assert "Duplicate column header" in exc_info.value.user_message

    # Duplicate headers with trailing whitespace
    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(b"score, score \n10,20\n")
    assert exc_info.value.code == ErrorCode.INVALID_CSV

    # Empty column header
    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(b"col1,,col3\n1,2,3\n")
    assert exc_info.value.code == ErrorCode.INVALID_CSV


def test_t03_malformed_rows_rejected() -> None:
    """T03: Rows with extra or missing fields must be rejected with row location."""
    # Row 2 has 2 fields instead of 3
    malformed = b"a,b,c\n1,2,3\n4,5\n"
    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(malformed)
    assert exc_info.value.code == ErrorCode.INVALID_CSV
    assert "Malformed row at data line 2" in exc_info.value.user_message


def test_t04_row_limit_boundary_and_rejection() -> None:
    """T04: Table exceeding 20,000 rows must be strictly rejected without silent truncation."""
    # Create header + 20,001 data rows
    buffer = io.StringIO()
    buffer.write("val\n")
    for i in range(20001):
        buffer.write(f"{i}\n")
    oversized = buffer.getvalue().encode("utf-8")

    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(oversized)
    assert exc_info.value.code == ErrorCode.DATASET_LIMIT_EXCEEDED
    assert "20,000 rows" in exc_info.value.user_message


def test_t04_column_limit_rejection() -> None:
    """T04: Dataset with more than 100 columns must be rejected."""
    cols = [f"c_{i}" for i in range(101)]
    header = ",".join(cols) + "\n"
    row = ",".join(["1"] * 101) + "\n"
    data = (header + row).encode("utf-8")

    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(data)
    assert exc_info.value.code == ErrorCode.DATASET_LIMIT_EXCEEDED
    assert "100 columns" in exc_info.value.user_message


def test_t04_cell_string_length_limit() -> None:
    """T04: Text cell exceeding 1,000 characters must be rejected."""
    long_string = "x" * 1001
    data = f"id,text\n1,{long_string}\n".encode("utf-8")

    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(data)
    assert exc_info.value.code == ErrorCode.DATASET_LIMIT_EXCEEDED
    assert "1,000 character limit" in exc_info.value.user_message


def test_t05_infinite_numeric_values_rejected() -> None:
    """T05: ±infinity values in numeric columns must be rejected with location."""
    data = b"id,val\n1,10.5\n2,inf\n"
    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(data)
    assert exc_info.value.code == ErrorCode.INVALID_CSV
    assert "Non-finite float" in exc_info.value.user_message

    data_neg = b"id,val\n1,-infinity\n"
    with pytest.raises(ServiceError) as exc_info:
        validate_and_parse_csv(data_neg)
    assert exc_info.value.code == ErrorCode.INVALID_CSV


def test_t05_missing_cell_token_handling() -> None:
    """T05: Documented null tokens become None while valid category tokens like 'NA' remain strings."""
    data = b"id,category,null_col\n1,NA,NaN\n2,normal,\n3,None,null\n"
    parsed = validate_and_parse_csv(data)
    df = parsed.df

    # 'NA' must NOT be converted to null
    assert df.loc[0, "category"] == "NA"
    assert df.loc[1, "category"] == "normal"
    assert pd.isna(df.loc[2, "category"])

    # NaN, empty string, and null are nulls
    assert df.loc[0, "null_col"] is None or pd.isna(df.loc[0, "null_col"])
    assert df.loc[1, "null_col"] is None or pd.isna(df.loc[1, "null_col"])
    assert df.loc[2, "null_col"] is None or pd.isna(df.loc[2, "null_col"])
