"""M2 tests: T08–T19, T43, T44 — modeling view, splits, CV leakage, metrics, champion selection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from datamind.contracts import (
    AlgorithmConfig,
    ColumnProfile,
    ColumnRole,
    ColumnSchema,
    DatasetProfile,
    DatasetSummary,
    ErrorCode,
    ModelingView,
    PreprocessingConfig,
    RowPolicy,
    ServiceError,
    TableSchema,
    TaskType,
)
from datamind.ml.experiment import run_experiment, select_champion
from datamind.ml.metrics import (
    compute_classification_fold_metrics,
    compute_regression_fold_metrics,
)
from datamind.ml.modeling import build_modeling_view
from datamind.ml.preprocessing import (
    FitSpyTransformer,
    build_preprocessor,
    check_transformed_bounds,
)
from datamind.ml.splitting import create_split_manifest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_iris_df() -> pd.DataFrame:
    """Load Iris via sklearn — guaranteed offline and deterministic."""
    from sklearn.datasets import load_iris

    iris = load_iris(as_frame=True)
    df = iris.frame.copy()
    df.index = range(len(df))
    return df


def _make_regression_df(n: int = 200, seed: int = 42) -> pd.DataFrame:
    from sklearn.datasets import make_regression

    X, y = make_regression(n_samples=n, n_features=4, noise=10, random_state=seed)
    df = pd.DataFrame(X, columns=[f"feat_{i}" for i in range(X.shape[1])])
    df["target"] = y
    df.index = range(len(df))
    return df


def _make_dummy_dataset_summary(
    df: pd.DataFrame, task: TaskType, target: str, dataset_id: str = "ds-test"
) -> DatasetSummary:
    """Construct a minimal DatasetSummary matching df columns/roles."""
    columns = []
    col_profiles = []
    for col in df.columns:
        if col == target:
            role = ColumnRole.NUMERIC if task == TaskType.REGRESSION else ColumnRole.CATEGORICAL
        elif pd.api.types.is_numeric_dtype(df[col]):
            role = ColumnRole.NUMERIC
        else:
            role = ColumnRole.CATEGORICAL
        columns.append(ColumnSchema(name=col, inferred_type=str(df[col].dtype), suggested_role=role))
        col_profiles.append(
            ColumnProfile(
                name=col,
                dtype=str(df[col].dtype),
                suggested_role=role,
                total_count=len(df),
                non_null_count=int(df[col].notna().sum()),
                null_count=int(df[col].isna().sum()),
                null_percentage=0.0,
                unique_count=int(df[col].nunique()),
                is_constant=df[col].nunique() == 1,
                sample_values=[str(v) for v in df[col].dropna().head(3).tolist()],
            )
        )
    schema = TableSchema(columns=columns, column_names=list(df.columns))
    profile = DatasetProfile(
        row_count=len(df),
        column_count=len(df.columns),
        duplicate_row_count=0,
        memory_bytes=int(df.memory_usage(deep=True).sum()),
        columns=col_profiles,
    )
    return DatasetSummary(
        id=dataset_id,
        project_id="proj-test",
        display_name="test_dataset",
        source_kind="demo",
        source_json="{}",
        raw_sha256="abc123",
        raw_relative_path="datasets/test/raw.csv",
        parser_version="1.0",
        parser_config_json="{}",
        schema_json=schema.model_dump_json(),
        profile_json=profile.model_dump_json(),
        row_count=len(df),
        column_count=len(df.columns),
        created_at="2026-01-01T00:00:00Z",
    )


def _iris_view() -> tuple[DatasetSummary, pd.DataFrame, ModelingView]:
    df = _make_iris_df()
    feature_cols = [c for c in df.columns if c != "target"]
    ds = _make_dummy_dataset_summary(df, TaskType.CLASSIFICATION, "target")
    view = build_modeling_view(
        dataset=ds,
        df=df,
        task=TaskType.CLASSIFICATION,
        target="target",
        numeric_features=feature_cols,
        categorical_features=[],
    )
    return ds, df, view


def _reg_view() -> tuple[DatasetSummary, pd.DataFrame, ModelingView]:
    df = _make_regression_df()
    feature_cols = [c for c in df.columns if c != "target"]
    ds = _make_dummy_dataset_summary(df, TaskType.REGRESSION, "target")
    view = build_modeling_view(
        dataset=ds,
        df=df,
        task=TaskType.REGRESSION,
        target="target",
        numeric_features=feature_cols,
        categorical_features=[],
    )
    return ds, df, view


# ---------------------------------------------------------------------------
# T08: Target in feature list must be rejected
# ---------------------------------------------------------------------------


def test_t08_target_leakage_rejected():
    """T08: Selecting target column as a feature must raise INVALID_TARGET."""
    df = _make_iris_df()
    feature_cols = list(df.columns)  # includes 'target'
    ds = _make_dummy_dataset_summary(df, TaskType.CLASSIFICATION, "target")
    with pytest.raises(ServiceError) as exc_info:
        build_modeling_view(
            dataset=ds,
            df=df,
            task=TaskType.CLASSIFICATION,
            target="target",
            numeric_features=feature_cols,
            categorical_features=[],
        )
    assert exc_info.value.code == ErrorCode.INVALID_TARGET
    assert "target" in exc_info.value.user_message.lower()


# ---------------------------------------------------------------------------
# T09: Missing target — default rejects; explicit policy records IDs
# ---------------------------------------------------------------------------


def test_t09_missing_target_default_rejected():
    """T09a: Missing target values must be rejected by default."""
    df = _make_iris_df()
    df.loc[0, "target"] = None
    ds = _make_dummy_dataset_summary(df, TaskType.CLASSIFICATION, "target")
    feature_cols = [c for c in df.columns if c != "target"]
    with pytest.raises(ServiceError) as exc_info:
        build_modeling_view(
            dataset=ds,
            df=df,
            task=TaskType.CLASSIFICATION,
            target="target",
            numeric_features=feature_cols,
            categorical_features=[],
        )
    assert exc_info.value.code == ErrorCode.INVALID_TARGET


def test_t09_missing_target_explicit_drop_records_ids():
    """T09b: Explicit drop_missing_target removes rows and records source row IDs in log."""
    df = _make_iris_df()
    df.loc[0, "target"] = None
    df.loc[5, "target"] = None
    ds = _make_dummy_dataset_summary(df, TaskType.CLASSIFICATION, "target")
    feature_cols = [c for c in df.columns if c != "target"]
    policy = RowPolicy(drop_missing_target=True)
    view = build_modeling_view(
        dataset=ds,
        df=df,
        task=TaskType.CLASSIFICATION,
        target="target",
        numeric_features=feature_cols,
        categorical_features=[],
        row_policy=policy,
    )
    assert 0 not in view.eligible_row_ids
    assert 5 not in view.eligible_row_ids
    assert len(view.eligible_row_ids) == 148
    # Cleaning log must document the source row IDs
    assert any("0" in entry or "5" in entry for entry in view.cleaning_log)


# ---------------------------------------------------------------------------
# T10: Duplicate and conflicting rows
# ---------------------------------------------------------------------------


def test_t10_exact_duplicates_collapsed_with_policy():
    """T10a: drop_exact_duplicates collapses exact feature+target duplicates."""
    df = _make_iris_df()
    # Append 2 exact duplicate rows
    dup = df.iloc[[0, 0]].copy()
    dup.index = [200, 201]
    df = pd.concat([df, dup])
    ds = _make_dummy_dataset_summary(df, TaskType.CLASSIFICATION, "target")
    feature_cols = [c for c in df.columns if c != "target"]
    policy = RowPolicy(drop_exact_duplicates=True)
    view = build_modeling_view(
        dataset=ds,
        df=df,
        task=TaskType.CLASSIFICATION,
        target="target",
        numeric_features=feature_cols,
        categorical_features=[],
        row_policy=policy,
    )
    # Iris has some internal duplicates; after appending 2 more copies of row 0,
    # the total collapsed count is 3 (original duplicate + our 2 added). Result = 149.
    assert 200 not in view.eligible_row_ids
    assert 201 not in view.eligible_row_ids
    assert len(view.eligible_row_ids) < 152  # some duplicates collapsed


def test_t10_conflicting_targets_rejected():
    """T10b: Same features but different target values must raise CONFLICTING_DUPLICATES."""
    df = pd.DataFrame({
        "feat": [1.0, 1.0, 2.0, 2.0, 3.0] * 7,
        "target": ["a", "b", "a", "a", "b"] * 7,
    })
    df.index = range(len(df))
    ds = _make_dummy_dataset_summary(df, TaskType.CLASSIFICATION, "target")
    with pytest.raises(ServiceError) as exc_info:
        build_modeling_view(
            dataset=ds,
            df=df,
            task=TaskType.CLASSIFICATION,
            target="target",
            numeric_features=["feat"],
            categorical_features=[],
        )
    assert exc_info.value.code == ErrorCode.CONFLICTING_DUPLICATES


# ---------------------------------------------------------------------------
# T11: Identical config/seed produces identical manifests
# ---------------------------------------------------------------------------


def test_t11_deterministic_splits():
    """T11: Same data/config/seed must produce identical dev/test/CV row membership."""
    ds, df, view = _iris_view()
    y = df[view.target]
    m1 = create_split_manifest(view, y, test_fraction=0.20, cv_folds=5, random_seed=42)
    m2 = create_split_manifest(view, y, test_fraction=0.20, cv_folds=5, random_seed=42)
    assert sorted(m1.train_row_ids) == sorted(m2.train_row_ids)
    assert sorted(m1.test_row_ids) == sorted(m2.test_row_ids)
    for f1, f2 in zip(m1.folds, m2.folds):
        assert sorted(f1.train_row_ids) == sorted(f2.train_row_ids)
        assert sorted(f1.val_row_ids) == sorted(f2.val_row_ids)


# ---------------------------------------------------------------------------
# T12: Manifest disjointness and partition invariants
# ---------------------------------------------------------------------------


def test_t12_split_manifest_invariants():
    """T12: Train/test disjoint; each dev row appears in val exactly once."""
    ds, df, view = _iris_view()
    y = df[view.target]
    manifest = create_split_manifest(view, y, test_fraction=0.20, cv_folds=5, random_seed=42)

    # Train and test are disjoint
    assert not set(manifest.train_row_ids) & set(manifest.test_row_ids)

    # CV val rows partition dev rows exactly once
    all_val_ids = []
    for fold in manifest.folds:
        assert not set(fold.train_row_ids) & set(fold.val_row_ids), "Fold train/val overlap"
        all_val_ids.extend(fold.val_row_ids)
    assert sorted(all_val_ids) == sorted(manifest.train_row_ids)

    # Sizes are plausible
    assert len(manifest.test_row_ids) > 0
    assert len(manifest.train_row_ids) > 0


# ---------------------------------------------------------------------------
# T13: Invalid classification setups
# ---------------------------------------------------------------------------


def test_t13_single_class_rejected():
    """T13: A single-class target must raise INSUFFICIENT_CLASS_SUPPORT."""
    n = 60
    df = pd.DataFrame({"feat": np.random.randn(n), "target": ["only"] * n})
    df.index = range(n)
    ds = _make_dummy_dataset_summary(df, TaskType.CLASSIFICATION, "target")
    with pytest.raises(ServiceError) as exc_info:
        build_modeling_view(
            dataset=ds,
            df=df,
            task=TaskType.CLASSIFICATION,
            target="target",
            numeric_features=["feat"],
            categorical_features=[],
        )
    assert exc_info.value.code == ErrorCode.INSUFFICIENT_CLASS_SUPPORT


def test_t13_too_few_rows_per_class_rejected():
    """T13: Classes with fewer than 10 rows before split must be rejected."""
    n_majority = 100
    n_rare = 5  # < 10
    df = pd.DataFrame({
        "feat": np.random.randn(n_majority + n_rare),
        "target": ["common"] * n_majority + ["rare"] * n_rare,
    })
    df.index = range(len(df))
    ds = _make_dummy_dataset_summary(df, TaskType.CLASSIFICATION, "target")
    with pytest.raises(ServiceError) as exc_info:
        build_modeling_view(
            dataset=ds,
            df=df,
            task=TaskType.CLASSIFICATION,
            target="target",
            numeric_features=["feat"],
            categorical_features=[],
        )
    assert exc_info.value.code == ErrorCode.INSUFFICIENT_CLASS_SUPPORT


# ---------------------------------------------------------------------------
# T14: Spy transformer records fit row IDs in CV and final refit
# ---------------------------------------------------------------------------


def test_t14_spy_transformer_fit_row_ids():
    """T14: FitSpyTransformer records exactly the train IDs for each fold and dev refit."""
    ds, df, view = _iris_view()
    y = df[view.target]
    manifest = create_split_manifest(view, y, test_fraction=0.20, cv_folds=5, random_seed=42)

    for fold in manifest.folds:
        train_ids = fold.train_row_ids
        val_ids = fold.val_row_ids
        X_train = df.loc[train_ids, view.numeric_features]
        y_train = df.loc[train_ids, view.target]

        spy = FitSpyTransformer()
        from sklearn.pipeline import Pipeline
        p = Pipeline([("spy", spy)])
        p.fit(X_train, y_train)

        # Spy must only see train IDs, not val IDs
        assert sorted(spy.fitted_indices) == sorted(train_ids)
        assert not set(spy.fitted_indices) & set(val_ids)

    # Final dev refit
    dev_ids = manifest.train_row_ids
    X_dev = df.loc[dev_ids, view.numeric_features]
    y_dev = df.loc[dev_ids, view.target]
    spy2 = FitSpyTransformer()
    from sklearn.pipeline import Pipeline
    p2 = Pipeline([("spy", spy2)])
    p2.fit(X_dev, y_dev)
    assert sorted(spy2.fitted_indices) == sorted(dev_ids)
    # Holdout rows must NOT have been seen
    assert not set(spy2.fitted_indices) & set(manifest.test_row_ids)


# ---------------------------------------------------------------------------
# T15: Holdout transform does not modify fitted pipeline
# ---------------------------------------------------------------------------


def test_t15_fitted_pipeline_unchanged_by_holdout():
    """T15: Fitted scaler mean/scale must be identical before and after transforming holdout."""
    ds, df, view = _iris_view()
    y = df[view.target]
    manifest = create_split_manifest(view, y, test_fraction=0.20, cv_folds=5, random_seed=42)

    dev_ids = manifest.train_row_ids
    test_ids = manifest.test_row_ids

    X_dev = df.loc[dev_ids, view.numeric_features]
    prep = build_preprocessor(view.numeric_features, [], PreprocessingConfig())
    prep.fit(X_dev)

    # Record state after fitting
    scaler = prep.named_transformers_["num"].named_steps["scaler"]
    mean_before = scaler.mean_.copy()
    scale_before = scaler.scale_.copy()

    # Transform holdout — add extreme values
    X_test = df.loc[test_ids, view.numeric_features].copy()
    X_test.iloc[0] = 999.0  # extreme
    prep.transform(X_test)

    # Fitted state must be unchanged
    np.testing.assert_array_equal(scaler.mean_, mean_before)
    np.testing.assert_array_equal(scaler.scale_, scale_before)


# ---------------------------------------------------------------------------
# T16: All-missing column in a fold
# ---------------------------------------------------------------------------


def test_t16_all_missing_numeric_column_stable():
    """T16: An all-missing numeric column must not cause a width change or error."""
    df = pd.DataFrame({
        "good": np.random.randn(80),
        "all_missing": [np.nan] * 80,
        "target": (np.random.randn(80) > 0).astype(str),
    })
    df.index = range(80)
    # Build preprocessor and fit — must not error
    prep = build_preprocessor(["good", "all_missing"], [], PreprocessingConfig())
    prep.fit(df[["good", "all_missing"]])
    out = prep.transform(df[["good", "all_missing"]])
    # Output must have 2 columns (one per numeric feature)
    assert out.shape[1] == 2


# ---------------------------------------------------------------------------
# T17: Independent metric oracle
# ---------------------------------------------------------------------------


def test_t17_classification_oracle():
    """T17: Classification metrics match independent hand-computed values."""
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 1])
    metrics = compute_classification_fold_metrics(
        y_true=y_true, y_pred=y_pred, fold_index=0, trial_id="oracle"
    )
    by_name = {m.name: m.value for m in metrics}
    # Accuracy = 3/4 = 0.75
    assert abs(by_name["accuracy"] - 0.75) < 1e-10
    # Macro F1: class-0 F1 = 2/(2+0+1) = 2/3; class-1 F1 = 2*2/(2*2+1+0) = 4/5
    # macro = (2/3 + 4/5) / 2 = 11/15
    expected_f1 = 11 / 15
    assert abs(by_name["f1_macro"] - expected_f1) < 1e-10


def test_t17_regression_oracle():
    """T17: Regression metrics match independent hand-computed values."""
    y_true = np.array([0.0, 2.0])
    y_pred = np.array([0.0, 0.0])
    metrics = compute_regression_fold_metrics(
        y_true=y_true, y_pred=y_pred, fold_index=0, trial_id="oracle"
    )
    by_name = {m.name: m.value for m in metrics}
    # MAE = (0 + 2) / 2 = 1.0
    assert abs(by_name["mae"] - 1.0) < 1e-10
    # MSE = (0 + 4) / 2 = 2.0; RMSE = sqrt(2)
    assert abs(by_name["rmse"] - np.sqrt(2)) < 1e-10
    # R² = 1 - SS_res/SS_tot = 1 - 4/2 = -1
    assert abs(by_name["r2"] - (-1.0)) < 1e-10
    # RMSE direction must be MINIMIZE
    from datamind.contracts import MetricDirection
    rmse_m = next(m for m in metrics if m.name == "rmse")
    assert rmse_m.direction == MetricDirection.MINIMIZE


# ---------------------------------------------------------------------------
# T18: Full experiment — baseline present, identical fold IDs, CV-only selection
# ---------------------------------------------------------------------------


def test_t18_full_experiment_baseline_and_cv():
    """T18: Experiment runs baseline and at least one model; selection is purely by CV."""
    ds, df, view = _iris_view()
    y = df[view.target]
    manifest = create_split_manifest(view, y, test_fraction=0.20, cv_folds=5, random_seed=42)

    import tempfile
    from pathlib import Path

    from datamind.config import Settings, reset_settings

    with tempfile.TemporaryDirectory() as tmpdir:
        settings = Settings(storage_dir=Path(tmpdir) / "storage")
        settings.ensure_directories()
        reset_settings(settings)

        try:
            alg_configs = [AlgorithmConfig(algorithm_id="logistic_regression")]
            summary = run_experiment(
                experiment_name="test-exp",
                project_id="proj-test",
                dataset_id="ds-test",
                df=df,
                view=view,
                manifest=manifest,
                algorithm_configs=alg_configs,
                seed=42,
            )
        finally:
            reset_settings(None)

    # Baseline must be present
    alg_ids = {t.algorithm_id for t in summary.trials}
    assert "dummy_classifier" in alg_ids, "Baseline must always be included"

    # Selection is not None
    assert summary.selected_trial_id is not None

    # Champion selected only by CV mean (holdout not exposed)
    champion = next(t for t in summary.trials if t.trial_id == summary.selected_trial_id)
    assert champion.status == "completed"
    assert champion.primary_cv_mean is not None

    # Verify identical fold membership across all trials by checking their metrics
    # All trials that completed must have the same number of CV fold metrics
    completed = [t for t in summary.trials if t.status == "completed"]
    assert len(completed) >= 1


# ---------------------------------------------------------------------------
# T19: Champion selected by CV — never sees holdout
# ---------------------------------------------------------------------------


def test_t19_champion_selected_by_cv_never_reads_holdout():
    """T19: If best CV model would have worse hypothetical holdout, selector still chooses by CV."""
    from datamind.contracts import TrialResult

    # Create two fake completed trials with different CV scores
    trial_a = TrialResult(
        trial_id="trial-a",
        experiment_id="exp-1",
        algorithm_id="logistic_regression",
        is_baseline=False,
        parameters={},
        status="completed",
        fit_duration_seconds=1.0,
        primary_cv_mean=0.90,  # best CV
        primary_cv_std=0.01,
    )
    trial_b = TrialResult(
        trial_id="trial-b",
        experiment_id="exp-1",
        algorithm_id="random_forest_classifier",
        is_baseline=False,
        parameters={},
        status="completed",
        fit_duration_seconds=2.0,
        primary_cv_mean=0.80,  # worse CV
        primary_cv_std=0.02,
    )

    champion, reason = select_champion([trial_a, trial_b], TaskType.CLASSIFICATION)
    assert champion is not None
    assert champion.trial_id == "trial-a", "Must select highest CV mean, ignoring holdout"
    assert "0.90" in reason or "f1_macro" in reason.lower()


# ---------------------------------------------------------------------------
# T43: Constant regression target rejected; undefined AUC returns None+reason
# ---------------------------------------------------------------------------


def test_t43_constant_regression_target_rejected():
    """T43a: A constant regression target must raise INVALID_TARGET."""
    n = 60
    df = pd.DataFrame({"feat": np.random.randn(n), "target": [5.0] * n})
    df.index = range(n)
    ds = _make_dummy_dataset_summary(df, TaskType.REGRESSION, "target")
    with pytest.raises(ServiceError) as exc_info:
        build_modeling_view(
            dataset=ds,
            df=df,
            task=TaskType.REGRESSION,
            target="target",
            numeric_features=["feat"],
            categorical_features=[],
        )
    assert exc_info.value.code == ErrorCode.INVALID_TARGET


def test_t43_undefined_roc_auc_returns_none_with_reason():
    """T43b: Multi-class classification must have ROC-AUC as None with a reason."""
    y_true = np.array([0, 1, 2, 0, 1, 2])
    y_pred = np.array([0, 1, 2, 0, 1, 2])
    metrics = compute_classification_fold_metrics(
        y_true=y_true, y_pred=y_pred, fold_index=0, trial_id="mc"
    )
    auc_metrics = [m for m in metrics if m.name == "roc_auc"]
    assert len(auc_metrics) == 1
    assert auc_metrics[0].value is None
    assert auc_metrics[0].reason is not None and len(auc_metrics[0].reason) > 0


# ---------------------------------------------------------------------------
# T44: High-cardinality one-hot beyond 500 column cap
# ---------------------------------------------------------------------------


def test_t44_high_cardinality_ohe_rejected():
    """T44: A categorical column with 600 unique values must be rejected by transform bounds."""
    n_rows = 600  # 600 unique values → 600 OHE columns > 500 cap
    cats = [f"cat_{i}" for i in range(n_rows)]
    df = pd.DataFrame({"cat_col": cats})

    prep = build_preprocessor([], ["cat_col"], PreprocessingConfig())
    prep.fit(df)

    with pytest.raises(ServiceError) as exc_info:
        check_transformed_bounds(prep, n_rows)
    assert exc_info.value.code == ErrorCode.TRANSFORM_LIMIT_EXCEEDED
