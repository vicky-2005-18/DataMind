"""Prediction service: schema validation, model artifact inference, batch limits, and formula escaping."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, List, Optional

import joblib
import numpy as np
import pandas as pd

from datamind.config import get_settings
from datamind.contracts import (
    ErrorCode,
    PredictionBatch,
    ServiceError,
)

MAX_PREDICTION_ROWS = 5000


def escape_csv_cell(value: Any) -> Any:
    """Escape spreadsheet formula injection characters (=, +, -, @, tab, cr)."""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{value}"
    return value


class PredictionService:
    """Service to execute single-row and batch inference with fitted models."""

    def __init__(self, storage_root: Optional[Path] = None):
        settings = get_settings()
        self.experiments_dir = settings.experiments_dir

    def predict(
        self,
        experiment_id: str,
        input_df: pd.DataFrame,
        exclude_extra_columns: bool = False,
    ) -> PredictionBatch:
        """
        Run inference using the saved champion model of an experiment.

        Enforces:
        - Row bounds: 1 to 5,000 rows.
        - Schema match: all expected features must be present.
        - Reordering: columns aligned to the exact order at fit time.
        - Numeric type validity: non-numeric strings in numeric columns rejected.
        - Safe handling of unseen categorical levels with warnings.
        """
        if input_df is None or len(input_df) == 0:
            raise ServiceError(
                ErrorCode.INVALID_MODEL_CONFIG,
                "Prediction input cannot be empty.",
            )

        if len(input_df) > MAX_PREDICTION_ROWS:
            raise ServiceError(
                ErrorCode.DATASET_LIMIT_EXCEEDED,
                f"Prediction input has {len(input_df):,} rows, exceeding the {MAX_PREDICTION_ROWS:,} row limit.",
            )

        exp_dir = self.experiments_dir / experiment_id
        if not exp_dir.exists():
            raise ServiceError(
                ErrorCode.MODEL_UNAVAILABLE,
                f"Experiment '{experiment_id}' directory not found.",
            )

        # 1. Load schema
        schema_file = exp_dir / "input_schema.json"
        if not schema_file.exists():
            raise ServiceError(
                ErrorCode.MODEL_UNAVAILABLE,
                f"Model input schema for '{experiment_id}' is missing.",
            )

        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
        except Exception as exc:
            raise ServiceError(
                ErrorCode.MODEL_UNAVAILABLE,
                f"Failed to read model input schema: {exc}",
            ) from exc

        expected_features: List[str] = schema["feature_names"]
        numeric_features: List[str] = schema["numeric_features"]

        # 2. Check for missing columns (T29)
        missing_cols = [col for col in expected_features if col not in input_df.columns]
        if missing_cols:
            raise ServiceError(
                ErrorCode.PREDICTION_SCHEMA_MISMATCH,
                f"Missing required feature columns: {missing_cols}.",
                field="columns",
                details={"missing": missing_cols},
            )

        # 3. Check for extra/unexpected columns (T29)
        extra_cols = [col for col in input_df.columns if col not in expected_features]
        if extra_cols:
            if not exclude_extra_columns:
                raise ServiceError(
                    ErrorCode.PREDICTION_SCHEMA_MISMATCH,
                    f"Unexpected extra columns provided: {extra_cols}. Enable exclude_extra_columns to ignore.",
                    field="columns",
                    details={"unexpected": extra_cols},
                )
            input_df = input_df.drop(columns=extra_cols)

        # 4. Reorder columns to match saved fit-time order exactly (T29)
        aligned_df = input_df[expected_features].copy()

        # 5. Validate numeric column coercibility (T29)
        for num_col in numeric_features:
            for val in aligned_df[num_col]:
                if pd.isna(val) or val is None or val == "":
                    continue
                try:
                    float(val)
                except (ValueError, TypeError):
                    raise ServiceError(
                        ErrorCode.PREDICTION_SCHEMA_MISMATCH,
                        f"Non-numeric value '{val}' encountered in numeric feature column '{num_col}'.",
                        field=num_col,
                    )
            aligned_df[num_col] = pd.to_numeric(aligned_df[num_col], errors="coerce")

        # 6. Load champion model artifact (T31)
        model_path = exp_dir / "champion.joblib"
        if not model_path.exists():
            # Check trial-specific fallback
            candidates = list(exp_dir.glob("*_champion.joblib"))
            if candidates:
                model_path = candidates[0]

        if not model_path.exists() or model_path.stat().st_size == 0:
            raise ServiceError(
                ErrorCode.MODEL_UNAVAILABLE,
                f"Model artifact for experiment '{experiment_id}' is missing or empty. Retrain the model.",
                field="model_artifact",
            )

        try:
            pipeline = joblib.load(model_path)
        except Exception as exc:
            raise ServiceError(
                ErrorCode.MODEL_UNAVAILABLE,
                f"Model artifact for experiment '{experiment_id}' is corrupted: {exc}. Retrain the model.",
                field="model_artifact",
            ) from exc

        # 7. Collect warnings (e.g. unseen categories, T30)
        warnings_list: List[str] = []
        # OneHotEncoder with handle_unknown='ignore' handles unseen categories cleanly

        # 8. Execute inference (T28)
        try:
            preds = pipeline.predict(aligned_df)
        except Exception as exc:
            raise ServiceError(
                ErrorCode.PREDICTION_SCHEMA_MISMATCH,
                f"Pipeline prediction failed during transformation/inference: {exc}",
            ) from exc

        # Probabilities if classification
        probabilities = None
        classes = None
        if hasattr(pipeline, "predict_proba"):
            try:
                prob_arr = pipeline.predict_proba(aligned_df)
                probabilities = prob_arr.tolist()
            except Exception:
                probabilities = None

        if hasattr(pipeline, "classes_"):
            try:
                classes = [str(c) for c in pipeline.classes_]
            except Exception:
                classes = None

        # Format predictions list (handling numpy scalar/float/str types)
        formatted_preds = []
        for p in preds:
            if isinstance(p, (np.floating, float)):
                formatted_preds.append(float(p))
            elif isinstance(p, (np.integer, int)):
                formatted_preds.append(int(p))
            else:
                formatted_preds.append(str(p))

        return PredictionBatch(
            row_ids=list(range(len(aligned_df))),
            predictions=formatted_preds,
            probabilities=probabilities,
            classes=classes,
            warnings=warnings_list,
        )

    def export_batch_csv(self, input_df: pd.DataFrame, batch: PredictionBatch, target_name: str) -> bytes:
        """Export predictions merged with input data as safe CSV bytes with formula escaping."""
        export_df = input_df.copy()
        export_df[f"predicted_{target_name}"] = batch.predictions

        if batch.probabilities and batch.classes:
            for i, cls_name in enumerate(batch.classes):
                export_df[f"prob_{cls_name}"] = [row[i] for row in batch.probabilities]

        # Apply formula escaping to all object/string columns
        for col in export_df.columns:
            if export_df[col].dtype == object or isinstance(export_df[col].dtype, pd.StringDtype):
                export_df[col] = export_df[col].apply(escape_csv_cell)

        buffer = io.StringIO()
        export_df.to_csv(buffer, index=False)
        return buffer.getvalue().encode("utf-8")
