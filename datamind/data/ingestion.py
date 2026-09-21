"""Strict CSV ingestion, byte validation, decoding, and parsing."""

from __future__ import annotations

import csv
import hashlib
import io
from typing import Any, Dict, List, NamedTuple, Set

import numpy as np
import pandas as pd

from datamind.config import get_settings
from datamind.contracts import ErrorCode, ServiceError

# Documented missing value tokens according to DATA_CONTRACTS
# Explicitly does not include "NA" to prevent silently coercing valid category tokens
MISSING_TOKENS: Set[str] = {"", "nan", "NaN", "NAN", "null", "NULL", "None", "NONE"}

INFINITE_TOKENS: Set[str] = {"inf", "-inf", "+inf", "infinity", "-infinity", "+infinity", "INF", "-INF"}


class ParsedDataset(NamedTuple):
    """Result of successfully validated and parsed tabular CSV data."""

    df: pd.DataFrame
    raw_sha256: str
    raw_bytes: bytes
    parser_version: str
    parser_config: Dict[str, Any]
    row_count: int
    column_count: int


def validate_and_parse_csv(raw_bytes: bytes, filename: str = "upload.csv") -> ParsedDataset:
    """Validate byte limits, decode, and parse CSV strictly according to DataMind contracts."""
    settings = get_settings()

    # 1. Byte limit check
    if len(raw_bytes) > settings.max_upload_bytes:
        raise ServiceError(
            ErrorCode.DATASET_LIMIT_EXCEEDED,
            f"File size ({len(raw_bytes):,} bytes) exceeds the maximum upload limit of {settings.max_upload_mib} MiB.",
            details={"byte_count": len(raw_bytes), "max_bytes": settings.max_upload_bytes},
        )

    # 2. Decode UTF-8 or UTF-8-BOM
    encoding_used = "utf-8"
    try:
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            text = raw_bytes.decode("utf-8-sig")
            encoding_used = "utf-8-sig"
        else:
            text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ServiceError(
            ErrorCode.INVALID_CSV,
            "File cannot be decoded as UTF-8 or UTF-8-BOM. Please convert your file to standard UTF-8.",
            details={"error": str(exc)},
        ) from exc

    if not text.strip():
        raise ServiceError(
            ErrorCode.INVALID_CSV,
            "The uploaded CSV file is empty.",
        )

    # Compute raw sha256
    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()

    # 3. Parse CSV rows
    reader = csv.reader(io.StringIO(text), delimiter=",", skipinitialspace=False)

    try:
        header_raw = next(reader)
    except StopIteration:
        raise ServiceError(
            ErrorCode.INVALID_CSV,
            "The CSV file does not contain a header row.",
        )

    # Trim whitespace from header column names
    header = [col.strip() for col in header_raw]

    if not header:
        raise ServiceError(
            ErrorCode.INVALID_CSV,
            "The CSV header contains no column names.",
        )

    # Check for empty column names
    for idx, col in enumerate(header):
        if not col:
            raise ServiceError(
                ErrorCode.INVALID_CSV,
                f"Column header at position {idx + 1} is empty after trimming whitespace.",
            )

    # Check for duplicate column names
    seen_headers: Set[str] = set()
    for col in header:
        if col in seen_headers:
            raise ServiceError(
                ErrorCode.INVALID_CSV,
                f"Duplicate column header '{col}' detected. All column names must be unique.",
                field=col,
            )
        seen_headers.add(col)

    # Check column count limit
    if len(header) > settings.max_columns:
        raise ServiceError(
            ErrorCode.DATASET_LIMIT_EXCEEDED,
            f"Dataset has {len(header)} columns, which exceeds the limit of {settings.max_columns} columns.",
            details={"column_count": len(header), "max_columns": settings.max_columns},
        )

    # 4. Parse and validate data rows
    rows: List[List[Any]] = []
    row_idx = 0

    for raw_row in reader:
        # Ignore purely empty lines
        if not raw_row or (len(raw_row) == 1 and raw_row[0].strip() == ""):
            continue

        row_idx += 1

        # Check row count limit (strict reject, no silent truncation)
        if row_idx > settings.max_rows:
            raise ServiceError(
                ErrorCode.DATASET_LIMIT_EXCEEDED,
                f"Dataset exceeds the limit of {settings.max_rows:,} rows. "
                "DataMind does not silently truncate training tables.",
                details={"max_rows": settings.max_rows},
            )

        # Strict field count check
        if len(raw_row) != len(header):
            raise ServiceError(
                ErrorCode.INVALID_CSV,
                f"Malformed row at data line {row_idx}: expected {len(header)} fields, but found {len(raw_row)}.",
                details={"row_index": row_idx, "expected_fields": len(header), "actual_fields": len(raw_row)},
            )

        processed_row: List[Any] = []
        for col_idx, cell in enumerate(raw_row):
            # Check cell string length limit
            if len(cell) > 1000:
                raise ServiceError(
                    ErrorCode.DATASET_LIMIT_EXCEEDED,
                    f"Cell value in row {row_idx}, column '{header[col_idx]}' exceeds the 1,000 character limit.",
                    details={"row_index": row_idx, "column": header[col_idx], "length": len(cell)},
                )

            trimmed = cell.strip()
            # Check for invalid infinity tokens
            if trimmed in INFINITE_TOKENS:
                raise ServiceError(
                    ErrorCode.INVALID_CSV,
                    f"Non-finite float '{cell}' detected at row {row_idx}, column '{header[col_idx]}'. "
                    "Columns must contain finite numbers or nulls.",
                    field=header[col_idx],
                    details={"row_index": row_idx, "value": cell},
                )

            # Check missing tokens
            if trimmed in MISSING_TOKENS:
                processed_row.append(None)
            else:
                processed_row.append(trimmed)

        rows.append(processed_row)

    if not rows:
        raise ServiceError(
            ErrorCode.INVALID_CSV,
            "CSV contains a header line but no valid data rows.",
        )

    # Build DataFrame with stable 0-based source row index
    df = pd.DataFrame(rows, columns=header)
    df.index = pd.RangeIndex(start=0, stop=len(df), step=1)

    # Try inferring numeric columns safely without silent data loss
    for col in df.columns:
        series = df[col]
        non_nulls = series.dropna()
        if len(non_nulls) == 0:
            continue
        # Attempt conversion to numeric
        try:
            numeric_vals = pd.to_numeric(non_nulls, errors="raise")
            # Verify finite values
            if np.isinf(numeric_vals).any():
                raise ServiceError(
                    ErrorCode.INVALID_CSV,
                    f"Non-finite value encountered in column '{col}'.",
                    field=col,
                )
            # Reassign with float or int
            df[col] = pd.to_numeric(df[col], errors="coerce")
        except (ValueError, TypeError):
            # Remains string / object
            pass

    parser_config = {
        "encoding": encoding_used,
        "delimiter": ",",
        "has_header": True,
        "filename": filename,
    }

    return ParsedDataset(
        df=df,
        raw_sha256=raw_sha256,
        raw_bytes=raw_bytes,
        parser_version="1.0",
        parser_config=parser_config,
        row_count=len(df),
        column_count=len(header),
    )
