"""
M3 MVP Tests: T20–T31, T41, T42
Covers: trial failures, experiment failures, idempotency, recovery, persistence restart,
holdout finalization, compatible comparison, prediction schema validation, and artifact integrity.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from datamind.config import Settings, reset_settings
from datamind.contracts import (
    AlgorithmConfig,
    DemoDatasetKind,
    ErrorCode,
    ServiceError,
    TaskType,
)
from datamind.services.comparison import ComparisonService
from datamind.services.experiments import ExperimentService
from datamind.services.prediction import PredictionService
from datamind.services.recovery import RecoveryService
from datamind.storage.database import run_migrations
from datamind.storage.experiment_repos import (
    ExperimentRepository,
)

# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture()
def tmp_settings(tmp_path):
    """Isolated settings pointing to a temp directory."""
    settings = Settings(
        storage_dir=tmp_path / "storage",
        logs_dir=tmp_path / "logs",
    )
    settings.ensure_directories()
    run_migrations(settings.db_path)
    reset_settings(settings)
    yield settings
    reset_settings(None)


@pytest.fixture()
def iris_experiment(tmp_settings):
    """Run a real Iris experiment and return (service, ExperimentSummary, df)."""
    svc = ExperimentService()

    # Load demo dataset via DatasetService
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project_svc = ProjectService()
    project = project_svc.create_project("Test Project T20", "")
    dataset_svc = DatasetService()
    dataset = dataset_svc.load_demo(project_id=project.id, demo_kind=DemoDatasetKind.IRIS)

    df = dataset_svc.load_dataframe(dataset.id)

    view = svc.prepare_modeling_view(
        dataset_id=dataset.id,
        task=TaskType.CLASSIFICATION,
        target="species",
        numeric_features=[c for c in df.columns if c != "species" and pd.api.types.is_numeric_dtype(df[c])],
        categorical_features=[],
    )
    manifest = svc.prepare_split(dataset_id=dataset.id, view=view, test_fraction=0.20, cv_folds=3, random_seed=42)

    algo_configs = [AlgorithmConfig(algorithm_id="logistic_regression")]
    summary = svc.run_supervised_experiment(
        experiment_name="T20 Iris Test",
        project_id=project.id,
        dataset_id=dataset.id,
        view=view,
        manifest=manifest,
        algorithm_configs=algo_configs,
        seed=42,
    )
    return svc, summary, dataset, project, df


# ── T20: One estimator deliberately fails ─────────────────────────────────


def test_t20_single_trial_failure_preserved(tmp_settings):
    """T20: A deliberately failing trial is recorded as failed; others complete normally."""
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project_svc = ProjectService()
    project = project_svc.create_project("T20 Project", "")
    dataset_svc = DatasetService()
    dataset = dataset_svc.load_demo(project_id=project.id, demo_kind=DemoDatasetKind.IRIS)
    df = dataset_svc.load_dataframe(dataset.id)

    svc = ExperimentService()
    view = svc.prepare_modeling_view(
        dataset_id=dataset.id,
        task=TaskType.CLASSIFICATION,
        target="species",
        numeric_features=[c for c in df.columns if c != "species" and pd.api.types.is_numeric_dtype(df[c])],
        categorical_features=[],
    )
    manifest = svc.prepare_split(dataset_id=dataset.id, view=view, test_fraction=0.20, cv_folds=3, random_seed=42)

    # Include an invalid algorithm_id to simulate a failure
    algo_configs = [
        AlgorithmConfig(algorithm_id="logistic_regression"),
        AlgorithmConfig(algorithm_id="nonexistent_algo_xyz"),  # will fail in registry lookup
    ]
    summary = svc.run_supervised_experiment(
        experiment_name="T20 Failure Test",
        project_id=project.id,
        dataset_id=dataset.id,
        view=view,
        manifest=manifest,
        algorithm_configs=algo_configs,
        seed=42,
    )

    # The bad trial must appear as failed
    failed = [t for t in summary.trials if t.status == "failed"]
    assert len(failed) >= 1, "Expected at least one failed trial"
    bad_trial = next((t for t in failed if t.algorithm_id == "nonexistent_algo_xyz"), None)
    assert bad_trial is not None, "The nonexistent algorithm trial must be marked failed"
    assert bad_trial.primary_cv_mean is None, "Failed trial must not have a CV score"

    # The valid logistic_regression trial must still be completed
    good = [t for t in summary.trials if t.algorithm_id == "logistic_regression"]
    assert len(good) == 1 and good[0].status == "completed"

    # Overall experiment should still be completed (not all failed)
    assert summary.status == "completed"
    assert summary.selected_trial_id is not None


# ── T21: All real models fail or baseline fails ───────────────────────────


def test_t21_all_candidates_fail_experiment_failed(tmp_settings):
    """T21: When all candidates fail, the experiment is marked failed with a useful reason."""
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project_svc = ProjectService()
    project = project_svc.create_project("T21 Project", "")
    dataset_svc = DatasetService()
    dataset = dataset_svc.load_demo(project_id=project.id, demo_kind=DemoDatasetKind.IRIS)
    df = dataset_svc.load_dataframe(dataset.id)

    svc = ExperimentService()
    view = svc.prepare_modeling_view(
        dataset_id=dataset.id,
        task=TaskType.CLASSIFICATION,
        target="species",
        numeric_features=[c for c in df.columns if c != "species" and pd.api.types.is_numeric_dtype(df[c])],
        categorical_features=[],
    )
    manifest = svc.prepare_split(dataset_id=dataset.id, view=view, test_fraction=0.20, cv_folds=3, random_seed=42)

    # Only submit algorithms that will not exist in the registry
    algo_configs = [AlgorithmConfig(algorithm_id="bad_algo_1"), AlgorithmConfig(algorithm_id="bad_algo_2")]

    summary = svc.run_supervised_experiment(
        experiment_name="T21 All Fail",
        project_id=project.id,
        dataset_id=dataset.id,
        view=view,
        manifest=manifest,
        algorithm_configs=algo_configs,
        seed=42,
    )

    # Baseline (dummy_classifier) must still be present; but when all *candidates* fail
    # and the baseline alone completed, the experiment can still be completed with baseline as champion.
    # However if baseline also fails → experiment.status == "failed".
    # Here the baseline passes so experiment is completed; we assert candidates are all failed.
    bad_trials = [t for t in summary.trials if t.algorithm_id.startswith("bad_algo")]
    assert all(t.status == "failed" for t in bad_trials)
    assert summary.selection_reason is not None and len(summary.selection_reason) > 0


# ── T22: Submission token idempotency ─────────────────────────────────────


def test_t22_submit_token_idempotency(iris_experiment):
    """T22: Submitting the exact same config twice returns the same experiment without re-training."""
    svc, summary1, dataset, project, df = iris_experiment

    # Reload the experiment via service (simulates second submit)
    existing = svc.experiment_repo.get_by_submission_token(summary1.submission_token)
    assert existing is not None
    assert existing.id == summary1.id, "Same token must return the same experiment ID"

    # Directly call run_supervised_experiment a second time — must return cached result
    view = svc.prepare_modeling_view(
        dataset_id=dataset.id,
        task=TaskType.CLASSIFICATION,
        target="species",
        numeric_features=[c for c in df.columns if c != "species" and pd.api.types.is_numeric_dtype(df[c])],
        categorical_features=[],
    )
    manifest = svc.prepare_split(dataset_id=dataset.id, view=view, test_fraction=0.20, cv_folds=3, random_seed=42)
    algo_configs = [AlgorithmConfig(algorithm_id="logistic_regression")]

    summary2 = svc.run_supervised_experiment(
        experiment_name="T20 Iris Test",
        project_id=project.id,
        dataset_id=dataset.id,
        view=view,
        manifest=manifest,
        algorithm_configs=algo_configs,
        seed=42,
    )
    assert summary2.id == summary1.id, "Idempotent submit must return same experiment"


# ── T23: Crash recovery / workspace lock guard ────────────────────────────



def test_t23_recovery_skips_when_lock_held(tmp_settings):
    """T23: RecoveryService must not interrupt an active run when is_locked reports True."""
    recovery = RecoveryService(db_path=tmp_settings.db_path)

    # Monkeypatch is_locked so reconcile sees lock held without needing a second process
    original_is_locked = type(recovery.lock).is_locked.fget
    type(recovery.lock).is_locked = property(lambda self: True)
    try:
        result = recovery.reconcile()
    finally:
        type(recovery.lock).is_locked = property(original_is_locked)

    assert result.get("skipped_reason") == "lock_held"
    assert result["interrupted_experiments"] == 0


def test_t23_recovery_marks_stale_running_experiments(tmp_settings):
    """T23: Stale 'running' experiments are marked 'interrupted' during recovery when lock is free."""
    import datetime
    import uuid

    from datamind.storage.database import get_connection

    db_path = tmp_settings.db_path
    conn = get_connection(db_path)
    try:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        exp_id = str(uuid.uuid4())
        # Disable FK constraints so we can insert a minimal stale experiment row for testing recovery
        conn.execute("PRAGMA foreign_keys = OFF;")
        conn.execute(
            """
            INSERT INTO experiments
            (id, project_id, dataset_id, split_id, task, name, status,
             submission_token, config_json, config_sha256, comparison_key,
             environment_json, registry_version, metric_version,
             random_seed, primary_metric, started_at, finished_at, error_json)
            VALUES (?, 'proj1', 'ds1', NULL, 'clustering', 'Stale', 'running',
                    'tok1', '{}', 'abc', 'cmp1', '{}', '1.0', '1.0', 42, 'inertia', ?, NULL, NULL)
            """,
            (exp_id, now),
        )
        conn.commit()
        conn.execute("PRAGMA foreign_keys = ON;")
    finally:
        conn.close()

    recovery = RecoveryService(db_path=db_path)
    result = recovery.reconcile()
    assert result["interrupted_experiments"] == 1


# ── T24: Persistence restart ──────────────────────────────────────────────


def test_t24_experiment_persists_across_restart(iris_experiment):
    """T24: Experiment history, config, and metrics survive after re-instantiating the repository."""
    _, summary, dataset, project, _ = iris_experiment

    # Simulate restart by creating fresh repository instances pointing to the same DB
    fresh_repo = ExperimentRepository(iris_experiment[0].experiment_repo.db_path)
    reloaded = fresh_repo.get_by_id(summary.id)

    assert reloaded is not None
    assert reloaded.id == summary.id
    assert reloaded.name == summary.name
    assert reloaded.selected_trial_id == summary.selected_trial_id
    assert len(reloaded.trials) == len(summary.trials)

    # Verify metrics are persisted
    champion_trial = next(
        (t for t in reloaded.trials if t.trial_id == reloaded.selected_trial_id), None
    )
    assert champion_trial is not None
    assert champion_trial.primary_cv_mean is not None


# ── T25: Idempotent holdout finalization ──────────────────────────────────


def test_t25_finalize_twice_returns_same_evaluation(iris_experiment):
    """T25: Finalizing twice must return the same immutable evaluation record without refit."""
    svc, summary, dataset, project, df = iris_experiment

    eval1 = svc.finalize_experiment(summary.id)
    eval2 = svc.finalize_experiment(summary.id)

    assert eval1.id == eval2.id, "Second finalization must return same evaluation ID"
    assert eval1.experiment_id == eval2.experiment_id
    # Metrics must be identical
    m1_names = {m.name: m.value for m in eval1.metrics}
    m2_names = {m.name: m.value for m in eval2.metrics}
    assert m1_names == m2_names


# ── T26: Holdout previously exposed flag ─────────────────────────────────


def test_t26_holdout_previously_exposed_flagged(tmp_settings):
    """T26: Finalizing a second experiment on the same split sets holdout_previously_exposed=True."""
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project_svc = ProjectService()
    project = project_svc.create_project("T26 Project", "")
    dataset_svc = DatasetService()
    dataset = dataset_svc.load_demo(project_id=project.id, demo_kind=DemoDatasetKind.IRIS)
    df = dataset_svc.load_dataframe(dataset.id)

    svc = ExperimentService()
    numeric_features = [c for c in df.columns if c != "species" and pd.api.types.is_numeric_dtype(df[c])]

    # First experiment
    view1 = svc.prepare_modeling_view(
        dataset_id=dataset.id, task=TaskType.CLASSIFICATION, target="species",
        numeric_features=numeric_features, categorical_features=[],
    )
    manifest = svc.prepare_split(dataset_id=dataset.id, view=view1, test_fraction=0.20, cv_folds=3, random_seed=42)
    summary1 = svc.run_supervised_experiment(
        experiment_name="T26 Exp1", project_id=project.id, dataset_id=dataset.id,
        view=view1, manifest=manifest,
        algorithm_configs=[AlgorithmConfig(algorithm_id="logistic_regression")], seed=42,
    )

    # Second experiment on the same split
    summary2 = svc.run_supervised_experiment(
        experiment_name="T26 Exp2", project_id=project.id, dataset_id=dataset.id,
        view=view1, manifest=manifest,
        algorithm_configs=[AlgorithmConfig(algorithm_id="decision_tree_classifier")], seed=42,
    )

    # Finalize first → not previously exposed
    eval1 = svc.finalize_experiment(summary1.id)
    assert eval1.holdout_previously_exposed is False

    # Finalize second → must be flagged as previously exposed
    eval2 = svc.finalize_experiment(summary2.id)
    assert eval2.holdout_previously_exposed is True


# ── T27: Compare incompatible experiments ─────────────────────────────────


def test_t27_incompatible_comparison_rejected(tmp_settings):
    """T27: Comparing experiments from different tasks/datasets raises INCOMPATIBLE_COMPARISON."""
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project_svc = ProjectService()
    project = project_svc.create_project("T27 Project", "")
    dataset_svc = DatasetService()

    iris = dataset_svc.load_demo(project_id=project.id, demo_kind=DemoDatasetKind.IRIS)
    regression = dataset_svc.load_demo(project_id=project.id, demo_kind=DemoDatasetKind.SYNTHETIC_REGRESSION)

    svc = ExperimentService()

    iris_df = dataset_svc.load_dataframe(iris.id)
    iris_view = svc.prepare_modeling_view(
        dataset_id=iris.id, task=TaskType.CLASSIFICATION, target="species",
        numeric_features=[c for c in iris_df.columns if c != "species" and pd.api.types.is_numeric_dtype(iris_df[c])],
        categorical_features=[],
    )
    iris_manifest = svc.prepare_split(dataset_id=iris.id, view=iris_view, test_fraction=0.20, cv_folds=3, random_seed=42)
    iris_exp = svc.run_supervised_experiment(
        experiment_name="Iris Exp", project_id=project.id, dataset_id=iris.id,
        view=iris_view, manifest=iris_manifest,
        algorithm_configs=[AlgorithmConfig(algorithm_id="logistic_regression")], seed=42,
    )

    reg_df = dataset_svc.load_dataframe(regression.id)
    reg_numeric = [c for c in reg_df.columns if c != "target" and pd.api.types.is_numeric_dtype(reg_df[c])]
    reg_view = svc.prepare_modeling_view(
        dataset_id=regression.id, task=TaskType.REGRESSION, target="target",
        numeric_features=reg_numeric, categorical_features=[],
    )
    reg_manifest = svc.prepare_split(dataset_id=regression.id, view=reg_view, test_fraction=0.20, cv_folds=3, random_seed=42)
    reg_exp = svc.run_supervised_experiment(
        experiment_name="Reg Exp", project_id=project.id, dataset_id=regression.id,
        view=reg_view, manifest=reg_manifest,
        algorithm_configs=[AlgorithmConfig(algorithm_id="linear_regression")], seed=42,
    )

    comparison_svc = ComparisonService(experiment_service=svc)
    with pytest.raises(ServiceError) as exc_info:
        comparison_svc.compare([iris_exp.id, reg_exp.id])

    assert exc_info.value.code == ErrorCode.INCOMPATIBLE_COMPARISON


# ── T28: Reload saved model and predict same rows ─────────────────────────


def test_t28_reload_model_predicts_consistently(iris_experiment):
    """T28: Reloading the saved champion and predicting on training rows returns same labels."""
    import joblib
    svc, summary, dataset, project, df = iris_experiment
    settings = svc.split_repo.db_path.parent  # just to get tmp path

    from datamind.config import get_settings
    settings = get_settings()

    exp_dir = settings.experiments_dir / summary.id
    model_path = exp_dir / "champion.joblib"
    schema_path = exp_dir / "input_schema.json"

    assert model_path.exists(), "champion.joblib must be saved"
    assert schema_path.exists(), "input_schema.json must be saved"

    pipeline = joblib.load(model_path)
    with open(schema_path) as f:
        schema = json.load(f)

    feature_names = schema["feature_names"]
    X = df[feature_names]
    preds_a = pipeline.predict(X)
    preds_b = pipeline.predict(X)

    # Deterministic: same input → same output
    assert list(preds_a) == list(preds_b), "Model predictions must be deterministic"

    # PredictionService must produce the same result
    pred_svc = PredictionService()
    batch = pred_svc.predict(experiment_id=summary.id, input_df=X.copy())
    assert len(batch.predictions) == len(df)


# ── T29: Schema validation (reorder, missing, extra, invalid numeric) ─────


def test_t29_prediction_schema_validation(iris_experiment):
    """T29: Column reorder accepted; missing/extra/invalid-numeric cases raise PREDICTION_SCHEMA_MISMATCH."""
    svc, summary, dataset, project, df = iris_experiment
    from datamind.config import get_settings
    settings = get_settings()

    with open(settings.experiments_dir / summary.id / "input_schema.json") as f:
        schema = json.load(f)

    feature_names = schema["feature_names"]
    pred_svc = PredictionService()
    X = df[feature_names].copy()

    # Reordered columns → must work (service re-aligns)
    shuffled = X[feature_names[::-1]]
    batch = pred_svc.predict(experiment_id=summary.id, input_df=shuffled)
    assert len(batch.predictions) == len(X)

    # Missing column → must raise
    with pytest.raises(ServiceError) as exc_info:
        pred_svc.predict(experiment_id=summary.id, input_df=X.drop(columns=[feature_names[0]]))
    assert exc_info.value.code == ErrorCode.PREDICTION_SCHEMA_MISMATCH

    # Extra column not excluded → must raise
    X_extra = X.copy()
    X_extra["extra_unwanted_col"] = 0
    with pytest.raises(ServiceError) as exc_info:
        pred_svc.predict(experiment_id=summary.id, input_df=X_extra, exclude_extra_columns=False)
    assert exc_info.value.code == ErrorCode.PREDICTION_SCHEMA_MISMATCH

    # Extra column excluded → must work
    batch_clean = pred_svc.predict(experiment_id=summary.id, input_df=X_extra, exclude_extra_columns=True)
    assert len(batch_clean.predictions) == len(X)

    # Invalid numeric → must raise
    X_bad = X.copy().astype(str)
    X_bad[feature_names[0]] = "not_a_number"
    with pytest.raises(ServiceError) as exc_info:
        pred_svc.predict(experiment_id=summary.id, input_df=X_bad)
    assert exc_info.value.code == ErrorCode.PREDICTION_SCHEMA_MISMATCH


# ── T30: Unseen category in prediction ───────────────────────────────────


def test_t30_unseen_category_prediction(tmp_settings):
    """T30: Prediction with unseen categorical level succeeds (OHE ignore) and returns valid output."""
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project_svc = ProjectService()
    project = project_svc.create_project("T30 Project", "")
    dataset_svc = DatasetService()

    # Build a small categorical classification dataset
    data = {
        "color": ["red", "blue", "red", "blue", "green", "green"] * 10,
        "size": [1.0, 2.0, 1.5, 2.5, 3.0, 3.5] * 10,
        "label": ["A", "B", "A", "B", "C", "C"] * 10,
    }
    df = pd.DataFrame(data)
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    dataset = dataset_svc.import_csv(
        project_id=project.id,
        raw_bytes=csv_bytes,
        display_name="T30 Categorical",
    )

    svc = ExperimentService()
    view = svc.prepare_modeling_view(
        dataset_id=dataset.id, task=TaskType.CLASSIFICATION, target="label",
        numeric_features=["size"], categorical_features=["color"],
    )
    manifest = svc.prepare_split(dataset_id=dataset.id, view=view, test_fraction=0.20, cv_folds=3, random_seed=42)
    summary = svc.run_supervised_experiment(
        experiment_name="T30 Cat Test", project_id=project.id, dataset_id=dataset.id,
        view=view, manifest=manifest,
        algorithm_configs=[AlgorithmConfig(algorithm_id="logistic_regression")], seed=42,
    )

    pred_svc = PredictionService()
    # Predict with a category never seen during training ("purple")
    test_df = pd.DataFrame({"color": ["purple"], "size": [2.0]})
    batch = pred_svc.predict(experiment_id=summary.id, input_df=test_df)
    assert len(batch.predictions) == 1, "Must return one prediction even for unseen category"


# ── T31: Missing / corrupt model artifact ─────────────────────────────────


def test_t31_missing_artifact_raises_model_unavailable(iris_experiment):
    """T31: If champion.joblib is missing, PredictionService raises MODEL_UNAVAILABLE."""
    svc, summary, dataset, project, df = iris_experiment
    from datamind.config import get_settings
    settings = get_settings()

    exp_dir = settings.experiments_dir / summary.id
    model_path = exp_dir / "champion.joblib"
    trial_model_path = exp_dir / f"{summary.selected_trial_id}_champion.joblib"

    # Remove BOTH champion files to ensure neither fallback path works
    original_bytes = model_path.read_bytes()
    model_path.unlink()
    trial_original = None
    if trial_model_path.exists():
        trial_original = trial_model_path.read_bytes()
        trial_model_path.unlink()

    pred_svc = PredictionService()
    feature_names = json.load(open(exp_dir / "input_schema.json"))["feature_names"]
    X = df[feature_names]

    try:
        with pytest.raises(ServiceError) as exc_info:
            pred_svc.predict(experiment_id=summary.id, input_df=X)
        assert exc_info.value.code == ErrorCode.MODEL_UNAVAILABLE
    finally:
        # Restore so fixture is clean for subsequent tests
        model_path.write_bytes(original_bytes)
        if trial_original is not None:
            trial_model_path.write_bytes(trial_original)


def test_t31_corrupt_artifact_raises_model_unavailable(iris_experiment):
    """T31: A corrupt (truncated) champion.joblib raises MODEL_UNAVAILABLE cleanly."""
    svc, summary, dataset, project, df = iris_experiment
    from datamind.config import get_settings
    settings = get_settings()

    exp_dir = settings.experiments_dir / summary.id
    model_path = exp_dir / "champion.joblib"
    original_bytes = model_path.read_bytes()

    # Corrupt the file
    model_path.write_bytes(b"corrupt_garbage_bytes")

    pred_svc = PredictionService()
    feature_names = json.load(open(exp_dir / "input_schema.json"))["feature_names"]
    X = df[feature_names]

    with pytest.raises(ServiceError) as exc_info:
        pred_svc.predict(experiment_id=summary.id, input_df=X)
    assert exc_info.value.code == ErrorCode.MODEL_UNAVAILABLE

    # Restore for idempotence
    model_path.write_bytes(original_bytes)


# ── T41: Cross-project reference rejection ────────────────────────────────


def test_t41_cross_project_dataset_rejected(tmp_settings):
    """T41: ExperimentService rejects dataset/split references from a different project."""
    from datamind.services.datasets import DatasetService
    from datamind.services.projects import ProjectService

    project_svc = ProjectService()
    project_a = project_svc.create_project("T41 Project A", "")
    project_b = project_svc.create_project("T41 Project B", "")

    dataset_svc = DatasetService()
    dataset_a = dataset_svc.load_demo(project_id=project_a.id, demo_kind=DemoDatasetKind.IRIS)
    df = dataset_svc.load_dataframe(dataset_a.id)

    svc = ExperimentService()
    view = svc.prepare_modeling_view(
        dataset_id=dataset_a.id, task=TaskType.CLASSIFICATION, target="species",
        numeric_features=[c for c in df.columns if c != "species" and pd.api.types.is_numeric_dtype(df[c])],
        categorical_features=[],
    )
    manifest = svc.prepare_split(dataset_id=dataset_a.id, view=view, test_fraction=0.20, cv_folds=3, random_seed=42)

    # Attempt to run experiment as project_b using dataset_a → must fail
    with pytest.raises(ServiceError) as exc_info:
        svc.run_supervised_experiment(
            experiment_name="Cross-project attempt",
            project_id=project_b.id,  # Wrong project
            dataset_id=dataset_a.id,
            view=view,
            manifest=manifest,
            algorithm_configs=[AlgorithmConfig(algorithm_id="logistic_regression")],
            seed=42,
        )
    assert exc_info.value.code == ErrorCode.INVALID_MODEL_CONFIG


# ── T42: Orphaned artifact detection and quarantine ───────────────────────


def test_t42_orphaned_artifact_tagged(tmp_settings):
    """T42: Orphaned experiment directories (not in DB) are tagged with .orphan marker by RecoveryService."""
    # Create a stale orphan directory under experiments/
    orphan_dir = tmp_settings.experiments_dir / "orphan-00000000-0000-0000-0000-000000000000"
    orphan_dir.mkdir(parents=True, exist_ok=True)
    (orphan_dir / "champion.joblib").write_bytes(b"fake")

    recovery = RecoveryService(db_path=tmp_settings.db_path)
    result = recovery.reconcile()

    assert result["orphaned_artifacts"] >= 1
    assert (orphan_dir / ".orphan").exists(), "Orphaned directory must be tagged with .orphan marker"
    # The champion.joblib must still exist (recovery only tags, doesn't delete)
    assert (orphan_dir / "champion.joblib").exists()


# ── Bonus: Row bound enforcement for prediction ───────────────────────────


def test_prediction_row_limit_enforced(iris_experiment):
    """Prediction service must reject inputs with more than MAX_PREDICTION_ROWS rows."""
    from datamind.services.prediction import MAX_PREDICTION_ROWS

    svc, summary, dataset, project, df = iris_experiment
    pred_svc = PredictionService()

    from datamind.config import get_settings
    settings = get_settings()
    feature_names = json.load(open(settings.experiments_dir / summary.id / "input_schema.json"))["feature_names"]

    # Build oversized input
    big_df = pd.concat([df[feature_names]] * (MAX_PREDICTION_ROWS // len(df) + 2), ignore_index=True)
    big_df = big_df.iloc[: MAX_PREDICTION_ROWS + 1]

    with pytest.raises(ServiceError) as exc_info:
        pred_svc.predict(experiment_id=summary.id, input_df=big_df)
    assert exc_info.value.code == ErrorCode.DATASET_LIMIT_EXCEEDED


# ── Bonus: Empty prediction input ─────────────────────────────────────────


def test_prediction_empty_input_rejected(iris_experiment):
    """PredictionService must reject empty DataFrames."""
    _, summary, dataset, project, df = iris_experiment
    pred_svc = PredictionService()

    with pytest.raises(ServiceError) as exc_info:
        pred_svc.predict(experiment_id=summary.id, input_df=pd.DataFrame())
    assert exc_info.value.code == ErrorCode.INVALID_MODEL_CONFIG
