"""Unfitted preprocessing pipeline factories and transform boundary guards."""

from __future__ import annotations

from typing import List

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, StandardScaler

from datamind.contracts import ErrorCode, PreprocessingConfig, ServiceError


class FitSpyTransformer(BaseEstimator, TransformerMixin):
    """Transformer for verification tests (T14) that records row IDs seen during fit."""

    def __init__(self) -> None:
        self.fitted_indices: List[int] = []

    def fit(self, X, y=None):
        if hasattr(X, "index"):
            self.fitted_indices = list(X.index)
        else:
            self.fitted_indices = list(range(len(X)))
        return self

    def transform(self, X):
        return X


def build_preprocessor(
    numeric_features: List[str],
    categorical_features: List[str],
    config: PreprocessingConfig,
) -> ColumnTransformer:
    """Construct an unfitted ColumnTransformer matching DataMind ML_SPEC."""
    transformers = []

    # Numeric pipeline
    if numeric_features:
        num_steps = []
        imputer_strategy = config.numeric_imputer if config.numeric_imputer in ("median", "mean") else "median"
        num_steps.append(
            ("imputer", SimpleImputer(strategy=imputer_strategy, keep_empty_features=True))
        )

        if config.numeric_scaler == "minmax":
            num_steps.append(("scaler", MinMaxScaler()))
        elif config.numeric_scaler == "passthrough":
            pass
        else:
            num_steps.append(("scaler", StandardScaler()))

        transformers.append(("num", Pipeline(num_steps), numeric_features))

    # Categorical pipeline
    if categorical_features:
        cat_steps = [
            (
                "imputer",
                SimpleImputer(strategy="constant", fill_value="missing"),
            ),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
        transformers.append(("cat", Pipeline(cat_steps), categorical_features))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def check_transformed_bounds(fitted_preprocessor: ColumnTransformer, sample_rows: int) -> None:
    """Verify that transformed feature dimensions do not exceed product limits (T44)."""
    # Max transformed columns: 500; Max transformed cells: 10,000,000
    try:
        feature_names = fitted_preprocessor.get_feature_names_out()
        n_cols = len(feature_names)
    except Exception:
        n_cols = 0

    if n_cols > 500:
        raise ServiceError(
            ErrorCode.TRANSFORM_LIMIT_EXCEEDED,
            f"Transformed matrix has {n_cols} columns, exceeding the maximum allowed limit of 500 columns. "
            "Please exclude high-cardinality features or choose numeric encoding.",
            details={"transformed_columns": n_cols, "max_columns": 500},
        )

    total_cells = n_cols * sample_rows
    if total_cells > 10_000_000:
        raise ServiceError(
            ErrorCode.TRANSFORM_LIMIT_EXCEEDED,
            f"Transformed feature matrix ({total_cells:,} cells) exceeds the 10,000,000 cell budget.",
            details={"cells": total_cells, "max_cells": 10_000_000},
        )


def build_full_pipeline(
    preprocessor: ColumnTransformer,
    estimator: BaseEstimator,
) -> Pipeline:
    """Combine an unfitted preprocessor and estimator into an executable scikit-learn Pipeline."""
    return Pipeline([("preprocess", preprocessor), ("model", estimator)])
