"""Task-appropriate ML metric calculations, aggregate statistics, and oracle verification."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)

from datamind.contracts import MetricDirection, MetricRecord, MetricScope


def compute_classification_fold_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray] = None,
    classes: Optional[List[Any]] = None,
    fold_index: int = -1,
    trial_id: str = "temp_trial",
) -> List[MetricRecord]:
    """Compute standard classification metrics on a fold or evaluation slice."""
    metrics: List[MetricRecord] = []

    # 1. Primary metric: macro F1
    f1_macro_val = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    metrics.append(
        MetricRecord(
            id=f"{trial_id}_f1_macro_{fold_index}",
            trial_id=trial_id,
            name="f1_macro",
            scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
            fold_index=fold_index,
            value=f1_macro_val,
            direction=MetricDirection.MAXIMIZE,
        )
    )

    # 2. Accuracy
    acc_val = float(accuracy_score(y_true, y_pred))
    metrics.append(
        MetricRecord(
            id=f"{trial_id}_accuracy_{fold_index}",
            trial_id=trial_id,
            name="accuracy",
            scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
            fold_index=fold_index,
            value=acc_val,
            direction=MetricDirection.MAXIMIZE,
        )
    )

    # 3. Balanced Accuracy
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    metrics.append(
        MetricRecord(
            id=f"{trial_id}_balanced_accuracy_{fold_index}",
            trial_id=trial_id,
            name="balanced_accuracy",
            scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
            fold_index=fold_index,
            value=bal_acc,
            direction=MetricDirection.MAXIMIZE,
        )
    )

    # 4. Precision & Recall macro
    prec_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    metrics.append(
        MetricRecord(
            id=f"{trial_id}_precision_macro_{fold_index}",
            trial_id=trial_id,
            name="precision_macro",
            scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
            fold_index=fold_index,
            value=prec_macro,
            direction=MetricDirection.MAXIMIZE,
        )
    )
    metrics.append(
        MetricRecord(
            id=f"{trial_id}_recall_macro_{fold_index}",
            trial_id=trial_id,
            name="recall_macro",
            scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
            fold_index=fold_index,
            value=rec_macro,
            direction=MetricDirection.MAXIMIZE,
        )
    )

    # 5. Optional Binary ROC-AUC (T43)
    unique_true = np.unique(y_true)
    if len(unique_true) == 2 and y_prob is not None:
        try:
            # Use positive class probabilities
            prob_pos = y_prob[:, 1] if y_prob.ndim == 2 and y_prob.shape[1] == 2 else y_prob
            auc_val = float(roc_auc_score(y_true, prob_pos))
            metrics.append(
                MetricRecord(
                    id=f"{trial_id}_roc_auc_{fold_index}",
                    trial_id=trial_id,
                    name="roc_auc",
                    scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
                    fold_index=fold_index,
                    value=auc_val,
                    direction=MetricDirection.MAXIMIZE,
                )
            )
        except Exception as exc:
            metrics.append(
                MetricRecord(
                    id=f"{trial_id}_roc_auc_{fold_index}",
                    trial_id=trial_id,
                    name="roc_auc",
                    scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
                    fold_index=fold_index,
                    value=None,
                    direction=MetricDirection.MAXIMIZE,
                    reason=f"METRIC_UNDEFINED: {exc}",
                )
            )
    elif len(unique_true) != 2:
        metrics.append(
            MetricRecord(
                id=f"{trial_id}_roc_auc_{fold_index}",
                trial_id=trial_id,
                name="roc_auc",
                scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
                fold_index=fold_index,
                value=None,
                direction=MetricDirection.MAXIMIZE,
                reason="METRIC_UNDEFINED: Binary ROC-AUC requires exactly 2 classes.",
            )
        )

    return metrics


def compute_regression_fold_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    fold_index: int = -1,
    trial_id: str = "temp_trial",
) -> List[MetricRecord]:
    """Compute standard regression metrics on a fold or evaluation slice."""
    metrics: List[MetricRecord] = []

    # 1. Primary metric: RMSE (strictly positive scale)
    mse_val = float(mean_squared_error(y_true, y_pred))
    rmse_val = float(math.sqrt(mse_val))
    metrics.append(
        MetricRecord(
            id=f"{trial_id}_rmse_{fold_index}",
            trial_id=trial_id,
            name="rmse",
            scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
            fold_index=fold_index,
            value=rmse_val,
            direction=MetricDirection.MINIMIZE,
        )
    )

    # 2. MAE
    mae_val = float(mean_absolute_error(y_true, y_pred))
    metrics.append(
        MetricRecord(
            id=f"{trial_id}_mae_{fold_index}",
            trial_id=trial_id,
            name="mae",
            scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
            fold_index=fold_index,
            value=mae_val,
            direction=MetricDirection.MINIMIZE,
        )
    )

    # 3. R2 score (unbounded below, can be negative)
    r2_val = float(r2_score(y_true, y_pred))
    metrics.append(
        MetricRecord(
            id=f"{trial_id}_r2_{fold_index}",
            trial_id=trial_id,
            name="r2",
            scope=MetricScope.CV_FOLD if fold_index >= 0 else MetricScope.HOLDOUT,
            fold_index=fold_index,
            value=r2_val,
            direction=MetricDirection.MAXIMIZE,
        )
    )

    return metrics


def aggregate_cv_metrics(
    fold_metrics: List[MetricRecord],
    trial_id: str,
) -> List[MetricRecord]:
    """Aggregate individual fold metrics into CV mean and standard deviation records."""
    grouped: Dict[str, List[float]] = {}
    directions: Dict[str, MetricDirection] = {}

    for m in fold_metrics:
        if m.value is not None:
            grouped.setdefault(m.name, []).append(m.value)
            directions[m.name] = m.direction

    agg_records: List[MetricRecord] = []
    for name, values in grouped.items():
        if not values:
            continue
        mean_val = float(np.mean(values))
        # Population standard deviation with ddof=0 per ML_SPEC
        std_val = float(np.std(values, ddof=0))

        details = {
            "fold_count": len(values),
            "fold_values": [round(v, 6) for v in values],
            "cv_std": round(std_val, 6),
        }

        agg_records.append(
            MetricRecord(
                id=f"{trial_id}_{name}_cv_mean",
                trial_id=trial_id,
                name=name,
                scope=MetricScope.CV_MEAN,
                fold_index=-1,
                value=mean_val,
                direction=directions[name],
                details_json=str(details),
            )
        )

    return agg_records
