"""Modeling view construction: task/target/feature validation and row policy application."""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional, Set

import numpy as np
import pandas as pd

from datamind.contracts import (
    ColumnRole,
    DatasetSummary,
    ErrorCode,
    ModelingView,
    RowPolicy,
    ServiceError,
    TableSchema,
    TaskType,
)

# Minimum eligible rows before any split
MIN_ELIGIBLE_ROWS = 30
# Classification: minimum rows per class before split
MIN_ROWS_PER_CLASS = 10
# Classification: 2–20 classes
MIN_CLASSES = 2
MAX_CLASSES = 20


def _infer_task_from_target(col_profile, schema: TableSchema) -> Optional[TaskType]:
    """Heuristic suggestion for task type given target column profile."""
    for col in schema.columns:
        if col.name == col_profile.name:
            if col.suggested_role == ColumnRole.NUMERIC:
                return TaskType.REGRESSION
            elif col.suggested_role in (ColumnRole.CATEGORICAL,):
                return TaskType.CLASSIFICATION
    return None


def build_modeling_view(
    dataset: DatasetSummary,
    df: pd.DataFrame,
    task: TaskType,
    target: str,
    numeric_features: List[str],
    categorical_features: List[str],
    row_policy: Optional[RowPolicy] = None,
) -> ModelingView:
    """
    Validate task/target/features, apply row policies, and build a ModelingView.

    Raises ServiceError for any configuration or data quality violations.
    """
    if row_policy is None:
        row_policy = RowPolicy()

    schema = dataset.get_schema()
    column_names: Set[str] = set(schema.column_names)

    # 1. Target column must exist
    if target not in column_names:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            f"Target column '{target}' not found in dataset columns.",
            field="target",
        )

    # 2. Target must not appear in features
    all_features: List[str] = numeric_features + categorical_features
    if target in all_features:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            f"Target column '{target}' must not appear in the feature list. Remove it from features.",
            field="target",
        )

    # 3. Feature set must not be empty
    if not all_features:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            "At least one feature must be selected.",
            field="features",
        )

    # 4. All feature columns must exist
    missing_cols = [f for f in all_features if f not in column_names]
    if missing_cols:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            f"Feature columns not found in dataset: {missing_cols}",
            field="features",
        )

    # 5. No feature column overlaps between numeric and categorical
    num_set = set(numeric_features)
    cat_set = set(categorical_features)
    overlap = num_set & cat_set
    if overlap:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            f"Columns appear in both numeric and categorical feature lists: {sorted(overlap)}",
            field="features",
        )

    cleaning_log: List[str] = []

    # 6. Handle missing target values
    y_full = df[target].copy()
    missing_target_mask = y_full.isna()
    missing_target_count = int(missing_target_mask.sum())

    if missing_target_count > 0:
        if not row_policy.drop_missing_target:
            raise ServiceError(
                ErrorCode.INVALID_TARGET,
                f"Column '{target}' has {missing_target_count} missing value(s). "
                "Set row_policy.drop_missing_target=True to remove these rows.",
                field="target",
                details={"missing_target_count": missing_target_count},
            )
        else:
            dropped_ids = list(df.index[missing_target_mask])
            cleaning_log.append(
                f"Dropped {missing_target_count} rows with missing target: source row IDs {dropped_ids[:10]}"
                + (f" ... (and {len(dropped_ids) - 10} more)" if len(dropped_ids) > 10 else "")
            )
            df = df[~missing_target_mask].copy()
            y_full = df[target].copy()

    # 7. Task-specific target validation
    if task == TaskType.REGRESSION:
        # Target must be numeric and finite
        numeric_target = pd.to_numeric(y_full, errors="coerce")
        non_numeric = int(numeric_target.isna().sum()) - int(y_full.isna().sum())
        if non_numeric > 0 or not np.isfinite(numeric_target.dropna()).all():
            raise ServiceError(
                ErrorCode.INVALID_TARGET,
                f"Regression target '{target}' must be a finite numeric column.",
                field="target",
            )
        if numeric_target.dropna().nunique() < 2:
            raise ServiceError(
                ErrorCode.INVALID_TARGET,
                f"Regression target '{target}' has fewer than 2 distinct values. "
                "A constant target cannot be modeled.",
                field="target",
            )
        # Re-assign to coerced
        df = df.copy()
        df[target] = numeric_target

    elif task == TaskType.CLASSIFICATION:
        unique_classes = y_full.dropna().unique()
        n_classes = len(unique_classes)
        if n_classes < MIN_CLASSES:
            raise ServiceError(
                ErrorCode.INSUFFICIENT_CLASS_SUPPORT,
                f"Classification requires at least {MIN_CLASSES} classes. "
                f"Target '{target}' has only {n_classes} unique value(s).",
                field="target",
            )
        if n_classes > MAX_CLASSES:
            raise ServiceError(
                ErrorCode.INSUFFICIENT_CLASS_SUPPORT,
                f"Classification supports at most {MAX_CLASSES} classes. "
                f"Target '{target}' has {n_classes} classes.",
                field="target",
            )

    # 8. Handle exact duplicate rows (feature+target)
    feature_target_cols = all_features + [target]
    available_cols = [c for c in feature_target_cols if c in df.columns]
    dup_mask = df[available_cols].duplicated(keep="first")
    exact_dup_count = int(dup_mask.sum())

    if exact_dup_count > 0:
        if not row_policy.drop_exact_duplicates:
            cleaning_log.append(
                f"Warning: {exact_dup_count} duplicate (feature+target) row(s) detected. "
                "Set row_policy.drop_exact_duplicates=True to collapse them."
            )
        else:
            df = df[~dup_mask].copy()
            cleaning_log.append(
                f"Collapsed {exact_dup_count} exact duplicate (feature+target) row(s)."
            )

    # 9. Reject conflicting duplicates (same features, different target)
    if all_features:
        feature_groups = df.groupby(all_features, dropna=False)[target].nunique()
        conflicting = feature_groups[feature_groups > 1]
        if len(conflicting) > 0:
            raise ServiceError(
                ErrorCode.CONFLICTING_DUPLICATES,
                f"Found {len(conflicting)} feature vector(s) with conflicting target values. "
                "Resolve these rows before modeling.",
                details={"conflicting_vectors": len(conflicting)},
            )

    # 10. Minimum eligible rows
    eligible_row_ids = list(df.index)
    n_eligible = len(eligible_row_ids)
    if n_eligible < MIN_ELIGIBLE_ROWS:
        raise ServiceError(
            ErrorCode.INSUFFICIENT_CLASS_SUPPORT,
            f"Only {n_eligible} eligible rows after filtering. Minimum required is {MIN_ELIGIBLE_ROWS}.",
        )

    # 11. Classification: check per-class support
    if task == TaskType.CLASSIFICATION:
        y_eligible = df[target]
        class_counts: Dict[str, int] = y_eligible.value_counts().to_dict()
        insufficient = {
            cls: cnt for cls, cnt in class_counts.items() if cnt < MIN_ROWS_PER_CLASS
        }
        if insufficient:
            raise ServiceError(
                ErrorCode.INSUFFICIENT_CLASS_SUPPORT,
                f"Classes with fewer than {MIN_ROWS_PER_CLASS} rows: {insufficient}. "
                "Add more data or exclude underrepresented classes.",
                details={"insufficient_classes": {str(k): v for k, v in insufficient.items()}},
            )

    # 12. Build deterministic view fingerprint
    fingerprint_payload = {
        "dataset_id": dataset.id,
        "task": task.value,
        "target": target,
        "numeric_features": sorted(numeric_features),
        "categorical_features": sorted(categorical_features),
        "eligible_row_ids": sorted(eligible_row_ids),
        "row_policy": row_policy.model_dump(),
    }
    view_fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return ModelingView(
        dataset_id=dataset.id,
        task=task,
        target=target,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        eligible_row_ids=eligible_row_ids,
        view_fingerprint=view_fingerprint,
        row_policy=row_policy,
        cleaning_log=cleaning_log,
    )
