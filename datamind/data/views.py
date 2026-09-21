"""Modeling view preparation, row policies, and target validation."""

from __future__ import annotations

import hashlib
import json
from typing import List

import numpy as np
import pandas as pd

from datamind.contracts import ErrorCode, ModelingView, RowPolicy, ServiceError, TaskType


def prepare_modeling_view(
    df: pd.DataFrame,
    dataset_id: str,
    task: TaskType,
    target: str,
    numeric_features: List[str],
    categorical_features: List[str],
    row_policy: RowPolicy,
) -> ModelingView:
    """Validate feature roles, apply row policies, and produce an immutable modeling view."""
    # 1. Target presence and role validation
    if target not in df.columns:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            f"Target column '{target}' was not found in dataset columns.",
            field=target,
        )

    # T08: Target leakage prevention - target cannot be a feature
    all_features = numeric_features + categorical_features
    if target in all_features:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            f"Target column '{target}' cannot be included in the feature list. DataMind prevents target leakage.",
            field=target,
        )

    # Disjoint feature lists check
    overlap = set(numeric_features).intersection(set(categorical_features))
    if overlap:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            f"Features cannot be both numeric and categorical: {overlap}",
        )

    if not all_features:
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            "At least one feature column must be selected for modeling.",
        )

    for feat in all_features:
        if feat not in df.columns:
            raise ServiceError(
                ErrorCode.UNSUPPORTED_FEATURE,
                f"Feature '{feat}' not found in dataset.",
                field=feat,
            )

    cleaning_log: List[str] = []
    view_df = df.copy()

    # 2. Target missing values (T09)
    target_series = view_df[target]
    missing_target_mask = target_series.isna()
    missing_target_count = int(missing_target_mask.sum())

    if missing_target_count > 0:
        if not row_policy.drop_missing_target:
            raise ServiceError(
                ErrorCode.INVALID_TARGET,
                f"Target column '{target}' contains {missing_target_count} missing values. "
                "Set drop_missing_target=True to drop these rows before modeling.",
                field=target,
                details={"missing_count": missing_target_count},
            )
        view_df = view_df[~missing_target_mask].copy()
        cleaning_log.append(
            f"Dropped {missing_target_count} rows with missing target '{target}'."
        )

    # 3. Conflicting duplicates and exact duplicates (T10)
    # Check conflicting targets on identical feature vectors
    feature_duplicates = view_df.duplicated(subset=all_features, keep=False)
    if feature_duplicates.any():
        # Check if identical features have different targets
        grouped = view_df[feature_duplicates].groupby(all_features)[target].nunique()
        conflicting = grouped[grouped > 1]
        if len(conflicting) > 0:
            raise ServiceError(
                ErrorCode.CONFLICTING_DUPLICATES,
                f"Detected {len(conflicting)} conflicting feature vectors with differing target values. "
                "Ambiguous records must be resolved before modeling.",
                details={"conflicting_groups": len(conflicting)},
            )

    # Collapse exact duplicates if policy enabled
    subset_all = all_features + [target]
    exact_duplicates_count = int(view_df.duplicated(subset=subset_all).sum())
    if exact_duplicates_count > 0:
        if row_policy.drop_exact_duplicates:
            view_df = view_df.drop_duplicates(subset=subset_all, keep="first").copy()
            cleaning_log.append(f"Collapsed {exact_duplicates_count} exact duplicate rows.")
        else:
            cleaning_log.append(f"Retained {exact_duplicates_count} exact duplicate rows per policy.")

    # 4. Minimum eligible rows check (T13)
    if len(view_df) < 30:
        raise ServiceError(
            ErrorCode.INSUFFICIENT_CLASS_SUPPORT,
            f"Dataset has only {len(view_df)} eligible rows after filtering. "
            "A minimum of 30 rows is required for cross-validation.",
            details={"eligible_rows": len(view_df), "min_required": 30},
        )

    # 5. Task-specific validation
    if task == TaskType.CLASSIFICATION:
        y_str = view_df[target].astype(str)
        class_counts = y_str.value_counts()
        n_classes = len(class_counts)

        if n_classes < 2:
            raise ServiceError(
                ErrorCode.INSUFFICIENT_CLASS_SUPPORT,
                f"Classification requires at least 2 distinct classes. Found only {n_classes}.",
                field=target,
            )
        if n_classes > 20:
            raise ServiceError(
                ErrorCode.INSUFFICIENT_CLASS_SUPPORT,
                f"Classification supports at most 20 classes. Found {n_classes}.",
                field=target,
            )

        # Minimum class support: 10 rows per class (T13)
        rare_classes = class_counts[class_counts < 10]
        if len(rare_classes) > 0:
            rare_detail = {str(k): int(v) for k, v in rare_classes.items()}
            raise ServiceError(
                ErrorCode.INSUFFICIENT_CLASS_SUPPORT,
                f"Classification requires at least 10 examples per class. Rare classes: {rare_detail}",
                field=target,
                details=rare_detail,
            )

    elif task == TaskType.REGRESSION:
        # Verify numeric target
        if not pd.api.types.is_numeric_dtype(view_df[target]):
            raise ServiceError(
                ErrorCode.INVALID_TARGET,
                f"Regression target '{target}' must be numeric. Found dtype: {view_df[target].dtype}",
                field=target,
            )

        # Check for non-finite values
        if not np.isfinite(view_df[target]).all():
            raise ServiceError(
                ErrorCode.INVALID_TARGET,
                f"Regression target '{target}' contains non-finite values (NaN or infinity).",
                field=target,
            )

        # Target distinct values >= 2 (T43)
        unique_targets = view_df[target].nunique()
        if unique_targets < 2:
            raise ServiceError(
                ErrorCode.INVALID_TARGET,
                f"Target column '{target}' has only {unique_targets} distinct value (constant). "
                "Regression requires at least 2 distinct target values.",
                field=target,
            )

    # 6. Build deterministic fingerprint
    eligible_row_ids = [int(idx) for idx in view_df.index]
    canonical_dict = {
        "dataset_id": dataset_id,
        "task": task.value,
        "target": target,
        "numeric_features": sorted(numeric_features),
        "categorical_features": sorted(categorical_features),
        "drop_missing_target": row_policy.drop_missing_target,
        "drop_exact_duplicates": row_policy.drop_exact_duplicates,
        "eligible_row_ids": eligible_row_ids,
    }
    view_fingerprint = hashlib.sha256(
        json.dumps(canonical_dict, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return ModelingView(
        dataset_id=dataset_id,
        task=task,
        target=target,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
        eligible_row_ids=eligible_row_ids,
        view_fingerprint=view_fingerprint,
        row_policy=row_policy,
        cleaning_log=cleaning_log,
    )
