"""Exact split and cross-validation fold manifest generation."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import List

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold, train_test_split

from datamind.config import get_settings
from datamind.contracts import (
    ErrorCode,
    FoldIndices,
    ModelingView,
    ServiceError,
    SplitManifest,
    TaskType,
)
from datamind.storage.artifacts import safe_relative_path, write_atomic_bytes


def create_split_manifest(
    view: ModelingView,
    y: pd.Series,
    test_fraction: float = 0.20,
    cv_folds: int = 5,
    random_seed: int = 42,
) -> SplitManifest:
    """Generate exact, reproducible development/holdout split and CV fold manifests."""
    if not (0.10 <= test_fraction <= 0.40):
        raise ServiceError(
            ErrorCode.INVALID_MODEL_CONFIG,
            f"Test fraction must be between 0.10 and 0.40. Got {test_fraction}.",
        )
    if cv_folds not in (3, 5):
        raise ServiceError(
            ErrorCode.INVALID_MODEL_CONFIG,
            f"CV folds must be 3 or 5. Got {cv_folds}.",
        )

    eligible_row_ids = np.array(view.eligible_row_ids)
    y_eligible = y.loc[eligible_row_ids]

    # Split into development and holdout test sets
    if view.task == TaskType.CLASSIFICATION:
        dev_ids, test_ids = train_test_split(
            eligible_row_ids,
            test_size=test_fraction,
            random_state=random_seed,
            stratify=y_eligible,
        )
    else:
        dev_ids, test_ids = train_test_split(
            eligible_row_ids,
            test_size=test_fraction,
            random_state=random_seed,
            shuffle=True,
        )

    dev_ids_list: List[int] = [int(x) for x in dev_ids]
    test_ids_list: List[int] = [int(x) for x in test_ids]

    # Verification: train and test sets must be disjoint
    if set(dev_ids_list).intersection(set(test_ids_list)):
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            "Integrity failure: Development and holdout sets share overlapping row IDs.",
        )

    # Cross-validation folds on development rows only
    dev_array = np.array(dev_ids_list)
    y_dev = y.loc[dev_array]

    if view.task == TaskType.CLASSIFICATION:
        splitter = StratifiedKFold(
            n_splits=cv_folds,
            shuffle=True,
            random_state=random_seed,
        )
        fold_gen = splitter.split(dev_array, y_dev)
    else:
        splitter = KFold(
            n_splits=cv_folds,
            shuffle=True,
            random_state=random_seed,
        )
        fold_gen = splitter.split(dev_array)

    folds: List[FoldIndices] = []
    validated_rows: List[int] = []

    for fold_idx, (train_pos, val_pos) in enumerate(fold_gen):
        fold_train_ids = [int(dev_array[p]) for p in train_pos]
        fold_val_ids = [int(dev_array[p]) for p in val_pos]

        # Invariant: fold train and val must be disjoint
        if set(fold_train_ids).intersection(set(fold_val_ids)):
            raise ServiceError(
                ErrorCode.INVALID_TARGET,
                f"Integrity failure: Fold {fold_idx} has overlapping train and validation sets.",
            )

        validated_rows.extend(fold_val_ids)
        folds.append(
            FoldIndices(
                fold_index=fold_idx,
                train_row_ids=fold_train_ids,
                val_row_ids=fold_val_ids,
            )
        )

    # Invariant: every dev row must be validated exactly once across all folds
    if sorted(validated_rows) != sorted(dev_ids_list):
        raise ServiceError(
            ErrorCode.INVALID_TARGET,
            "Integrity failure: Fold validation sets do not partition development rows exactly once.",
        )

    # Build canonical fingerprint
    canonical_split = {
        "view_fingerprint": view.view_fingerprint,
        "task": view.task.value,
        "target": view.target,
        "test_fraction": test_fraction,
        "cv_folds": cv_folds,
        "random_seed": random_seed,
        "train_row_ids": dev_ids_list,
        "test_row_ids": test_ids_list,
        "folds": [
            {
                "fold_index": f.fold_index,
                "train_row_ids": f.train_row_ids,
                "val_row_ids": f.val_row_ids,
            }
            for f in folds
        ],
    }
    split_fingerprint = hashlib.sha256(
        json.dumps(canonical_split, sort_keys=True).encode("utf-8")
    ).hexdigest()

    split_id = str(uuid.uuid4())
    settings = get_settings()
    split_dest_dir = settings.splits_dir / split_id
    split_dest_file = split_dest_dir / "manifest.json"

    manifest_bytes = json.dumps(canonical_split, indent=2, sort_keys=True).encode("utf-8")
    write_atomic_bytes(split_dest_file, manifest_bytes)
    manifest_rel_path = safe_relative_path(settings.storage_dir, split_dest_file)

    return SplitManifest(
        split_id=split_id,
        dataset_id=view.dataset_id,
        view_fingerprint=view.view_fingerprint,
        split_fingerprint=split_fingerprint,
        task=view.task,
        target=view.target,
        test_fraction=test_fraction,
        cv_folds=cv_folds,
        random_seed=random_seed,
        train_row_ids=dev_ids_list,
        test_row_ids=test_ids_list,
        folds=folds,
        manifest_relative_path=manifest_rel_path,
    )
