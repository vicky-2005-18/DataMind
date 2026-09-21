"""Experiment engine: CV training, champion selection, development refit, and persistence."""

from __future__ import annotations

import datetime
import hashlib
import json
import time
import uuid
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from datamind.config import get_settings
from datamind.contracts import (
    AlgorithmConfig,
    ErrorCode,
    ExperimentSummary,
    MetricDirection,
    MetricRecord,
    MetricScope,
    ModelingView,
    PreprocessingConfig,
    ServiceError,
    SplitManifest,
    TaskType,
    TrialResult,
)
from datamind.ml.metrics import (
    aggregate_cv_metrics,
    compute_classification_fold_metrics,
    compute_regression_fold_metrics,
)
from datamind.ml.preprocessing import (
    build_full_pipeline,
    build_preprocessor,
    check_transformed_bounds,
)
from datamind.ml.registry import (
    AlgorithmDescriptor,
    get_algorithm,
    get_baseline_for_task,
)

REGISTRY_VERSION = "1.0"
METRIC_VERSION = "1.0"


def _get_primary_metric(task: TaskType) -> str:
    if task == TaskType.CLASSIFICATION:
        return "f1_macro"
    elif task == TaskType.REGRESSION:
        return "rmse"
    raise ServiceError(ErrorCode.INVALID_MODEL_CONFIG, f"Unsupported task: {task}")


def _get_primary_direction(task: TaskType) -> MetricDirection:
    if task == TaskType.CLASSIFICATION:
        return MetricDirection.MAXIMIZE
    return MetricDirection.MINIMIZE


def _get_primary_cv_mean(metrics: List[MetricRecord], primary_metric: str) -> Optional[float]:
    """Extract the CV mean for the primary metric from a list of metric records."""
    for m in metrics:
        if m.scope == MetricScope.CV_MEAN and m.name == primary_metric:
            return m.value
    return None


def _get_primary_cv_std(metrics: List[MetricRecord], primary_metric: str) -> Optional[float]:
    for m in metrics:
        if m.scope == MetricScope.CV_MEAN and m.name == primary_metric:
            details = m.details_json
            try:
                d = json.loads(details.replace("'", '"'))
                return d.get("cv_std")
            except Exception:
                return None
    return None


def _compute_fold_metrics(
    task: TaskType,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: Optional[np.ndarray],
    fold_index: int,
    trial_id: str,
) -> List[MetricRecord]:
    if task == TaskType.CLASSIFICATION:
        return compute_classification_fold_metrics(
            y_true=y_true,
            y_pred=y_pred,
            y_prob=y_prob,
            fold_index=fold_index,
            trial_id=trial_id,
        )
    else:
        return compute_regression_fold_metrics(
            y_true=y_true,
            y_pred=y_pred,
            fold_index=fold_index,
            trial_id=trial_id,
        )


def _run_single_trial(
    trial_id: str,
    experiment_id: str,
    descriptor: AlgorithmDescriptor,
    params: Dict[str, Any],
    df: pd.DataFrame,
    view: ModelingView,
    manifest: SplitManifest,
    prep_config: PreprocessingConfig,
    seed: int,
) -> TrialResult:
    """
    Run full CV for one algorithm. Returns a TrialResult.
    Failures in individual folds make the trial failed (not averaged).
    """
    primary_metric = _get_primary_metric(view.task)
    start_time = time.monotonic()
    trial_warnings: List[str] = []
    all_fold_metrics: List[MetricRecord] = []

    try:
        descriptor.build_estimator(params, seed)
    except ServiceError:
        raise
    except Exception as exc:
        return TrialResult(
            trial_id=trial_id,
            experiment_id=experiment_id,
            algorithm_id=descriptor.algorithm_id,
            is_baseline=descriptor.is_baseline,
            parameters=params,
            status="failed",
            fit_duration_seconds=time.monotonic() - start_time,
            error=f"Estimator construction failed: {exc}",
        )

    # Run CV
    for fold in manifest.folds:
        fold_index = fold.fold_index
        train_ids = fold.train_row_ids
        val_ids = fold.val_row_ids

        X_train = df.loc[train_ids, view.numeric_features + view.categorical_features]
        y_train = df.loc[train_ids, view.target]
        X_val = df.loc[val_ids, view.numeric_features + view.categorical_features]
        y_val = df.loc[val_ids, view.target]

        # Build and fit a fresh pipeline for this fold
        preprocessor = build_preprocessor(
            numeric_features=view.numeric_features,
            categorical_features=view.categorical_features,
            config=prep_config,
        )
        estimator_fold = descriptor.build_estimator(params, seed)
        pipeline = build_full_pipeline(preprocessor, estimator_fold)

        with warnings.catch_warnings(record=True) as w_list:
            warnings.simplefilter("always")
            try:
                pipeline.fit(X_train, y_train)
            except Exception as exc:
                return TrialResult(
                    trial_id=trial_id,
                    experiment_id=experiment_id,
                    algorithm_id=descriptor.algorithm_id,
                    is_baseline=descriptor.is_baseline,
                    parameters=params,
                    status="failed",
                    fit_duration_seconds=time.monotonic() - start_time,
                    error=f"Fold {fold_index} fit failed: {exc}",
                )
            for warning in w_list:
                msg = str(warning.message)
                if msg not in trial_warnings:
                    trial_warnings.append(msg)

        # Check transform bounds on first fold
        if fold_index == 0:
            try:
                check_transformed_bounds(pipeline.named_steps["preprocess"], len(X_train))
            except ServiceError as exc:
                return TrialResult(
                    trial_id=trial_id,
                    experiment_id=experiment_id,
                    algorithm_id=descriptor.algorithm_id,
                    is_baseline=descriptor.is_baseline,
                    parameters=params,
                    status="failed",
                    fit_duration_seconds=time.monotonic() - start_time,
                    error=exc.user_message,
                )

        # Predict
        y_pred = pipeline.predict(X_val)
        y_prob: Optional[np.ndarray] = None
        if view.task == TaskType.CLASSIFICATION and hasattr(pipeline, "predict_proba"):
            try:
                y_prob = pipeline.predict_proba(X_val)
            except Exception:
                pass

        fold_mets = _compute_fold_metrics(
            task=view.task,
            y_true=y_val.to_numpy(),
            y_pred=y_pred,
            y_prob=y_prob,
            fold_index=fold_index,
            trial_id=trial_id,
        )
        all_fold_metrics.extend(fold_mets)

    # Aggregate CV metrics
    agg_metrics = aggregate_cv_metrics(all_fold_metrics, trial_id)
    all_metrics = all_fold_metrics + agg_metrics

    duration = time.monotonic() - start_time
    primary_cv_mean = _get_primary_cv_mean(agg_metrics, primary_metric)
    primary_cv_std = _get_primary_cv_std(agg_metrics, primary_metric)

    return TrialResult(
        trial_id=trial_id,
        experiment_id=experiment_id,
        algorithm_id=descriptor.algorithm_id,
        is_baseline=descriptor.is_baseline,
        parameters=params,
        status="completed",
        fit_duration_seconds=duration,
        warnings=trial_warnings[:10],
        metrics=all_metrics,
        primary_cv_mean=primary_cv_mean,
        primary_cv_std=primary_cv_std,
    )


def select_champion(
    trials: List[TrialResult],
    task: TaskType,
) -> Tuple[Optional[TrialResult], str]:
    """
    Select the best trial from completed trials using CV only.
    Order: primary CV mean → lower complexity_order → algorithm_id lexicographic.
    Returns (champion_trial, reason).
    """
    from datamind.ml.registry import REGISTRY

    primary_metric = _get_primary_metric(task)
    direction = _get_primary_direction(task)
    completed = [t for t in trials if t.status == "completed" and t.primary_cv_mean is not None]

    if not completed:
        return None, "No trial completed successfully."

    def sort_key(t: TrialResult):
        score = t.primary_cv_mean
        # For minimize direction (RMSE), lower is better → use positive score
        # For maximize direction (F1), higher is better → negate for min sort
        if direction == MetricDirection.MAXIMIZE:
            primary_key = -(score if score is not None else float("-inf"))
        else:
            primary_key = score if score is not None else float("inf")
        complexity = REGISTRY.get(t.algorithm_id, None)
        complexity_order = complexity.complexity_order if complexity else 999
        return (primary_key, complexity_order, t.algorithm_id)

    ranked = sorted(completed, key=sort_key)
    champion = ranked[0]
    baseline_trials = [t for t in completed if t.is_baseline]
    baseline = baseline_trials[0] if baseline_trials else None

    if baseline and champion.trial_id == baseline.trial_id:
        reason = (
            f"Baseline selected: no supervised model improved upon "
            f"baseline {primary_metric} CV mean ({champion.primary_cv_mean:.6f})."
        )
    else:
        reason = (
            f"Selected by highest {primary_metric} CV mean"
            if direction == MetricDirection.MAXIMIZE
            else f"Selected by lowest {primary_metric} CV mean"
        ) + f" = {champion.primary_cv_mean:.6f}."

    return champion, reason


def refit_champion(
    champion: TrialResult,
    df: pd.DataFrame,
    view: ModelingView,
    manifest: SplitManifest,
    prep_config: PreprocessingConfig,
    seed: int,
    experiment_dir: Path,
) -> Path:
    """
    Refit the champion pipeline on all development rows and save to disk.
    Returns the path to the saved pipeline artifact.
    """
    descriptor = get_algorithm(champion.algorithm_id)
    preprocessor = build_preprocessor(
        numeric_features=view.numeric_features,
        categorical_features=view.categorical_features,
        config=prep_config,
    )
    estimator = descriptor.build_estimator(champion.parameters, seed)
    pipeline = build_full_pipeline(preprocessor, estimator)

    dev_ids = manifest.train_row_ids
    feature_cols = view.numeric_features + view.categorical_features
    X_dev = df.loc[dev_ids, feature_cols]
    y_dev = df.loc[dev_ids, view.target]

    pipeline.fit(X_dev, y_dev)

    # Save champion model artifact
    model_path = experiment_dir / "champion.joblib"
    joblib.dump(pipeline, model_path)
    trial_model_path = experiment_dir / f"{champion.trial_id}_champion.joblib"
    joblib.dump(pipeline, trial_model_path)

    # Save input schema for runtime prediction validation
    schema_payload = {
        "feature_names": feature_cols,
        "numeric_features": view.numeric_features,
        "categorical_features": view.categorical_features,
        "expected_dtypes": {col: str(df[col].dtype) for col in feature_cols},
        "target": view.target,
        "task": view.task.value,
    }
    with open(experiment_dir / "input_schema.json", "w", encoding="utf-8") as f:
        json.dump(schema_payload, f, indent=2)

    # Save manifest summary
    manifest_payload = {
        "experiment_id": champion.experiment_id,
        "trial_id": champion.trial_id,
        "algorithm_id": champion.algorithm_id,
        "parameters": champion.parameters,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open(experiment_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    return model_path


def run_experiment(
    experiment_name: str,
    project_id: str,
    dataset_id: str,
    df: pd.DataFrame,
    view: ModelingView,
    manifest: SplitManifest,
    algorithm_configs: List[AlgorithmConfig],
    prep_config: Optional[PreprocessingConfig] = None,
    seed: int = 42,
) -> ExperimentSummary:
    """
    Run a full supervised experiment: CV all algorithms, select champion, refit on dev.
    Holdout is NOT scored here. Returns ExperimentSummary with all trial results.
    """
    if prep_config is None:
        prep_config = PreprocessingConfig()

    settings = get_settings()
    experiment_id = str(uuid.uuid4())
    primary_metric = _get_primary_metric(view.task)
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Build submission token from config hash
    config_payload = {
        "experiment_name": experiment_name,
        "project_id": project_id,
        "dataset_id": dataset_id,
        "view_fingerprint": view.view_fingerprint,
        "split_fingerprint": manifest.split_fingerprint,
        "algorithm_configs": [a.model_dump() for a in algorithm_configs],
        "prep_config": prep_config.model_dump(),
        "seed": seed,
    }
    config_json = json.dumps(config_payload, sort_keys=True)
    submission_token = hashlib.sha256(config_json.encode()).hexdigest()

    # Always include baseline
    baseline_descriptor = get_baseline_for_task(view.task)
    baseline_config = AlgorithmConfig(algorithm_id=baseline_descriptor.algorithm_id)

    # De-duplicate and ensure baseline is present
    seen_ids = set()
    final_configs: List[AlgorithmConfig] = [baseline_config]
    seen_ids.add(baseline_config.algorithm_id)
    for cfg in algorithm_configs:
        if cfg.algorithm_id not in seen_ids:
            final_configs.append(cfg)
            seen_ids.add(cfg.algorithm_id)

    # Run trials
    trials: List[TrialResult] = []
    for cfg in final_configs:
        trial_id = str(uuid.uuid4())
        try:
            descriptor = get_algorithm(cfg.algorithm_id)
            # Task mismatch guard
            if descriptor.task != view.task:
                trials.append(
                    TrialResult(
                        trial_id=trial_id,
                        experiment_id=experiment_id,
                        algorithm_id=cfg.algorithm_id,
                        is_baseline=descriptor.is_baseline,
                        parameters=cfg.parameters,
                        status="failed",
                        fit_duration_seconds=0.0,
                        error=f"Algorithm '{cfg.algorithm_id}' is for {descriptor.task.value}, "
                        f"not {view.task.value}.",
                    )
                )
                continue
            result = _run_single_trial(
                trial_id=trial_id,
                experiment_id=experiment_id,
                descriptor=descriptor,
                params=cfg.parameters,
                df=df,
                view=view,
                manifest=manifest,
                prep_config=prep_config,
                seed=seed,
            )
            trials.append(result)
        except ServiceError as exc:
            trials.append(
                TrialResult(
                    trial_id=trial_id,
                    experiment_id=experiment_id,
                    algorithm_id=cfg.algorithm_id,
                    is_baseline=False,
                    parameters=cfg.parameters,
                    status="failed",
                    fit_duration_seconds=0.0,
                    error=exc.user_message,
                )
            )
        except Exception as exc:
            trials.append(
                TrialResult(
                    trial_id=trial_id,
                    experiment_id=experiment_id,
                    algorithm_id=cfg.algorithm_id,
                    is_baseline=False,
                    parameters=cfg.parameters,
                    status="failed",
                    fit_duration_seconds=0.0,
                    error=f"Unexpected error: {type(exc).__name__}: {exc}",
                )
            )

    # Select champion from completed trials
    champion, selection_reason = select_champion(trials, view.task)

    # T21: Baseline failure or all candidate models failing causes overall experiment to fail
    baseline_trials = [t for t in trials if t.is_baseline]
    baseline_failed = len(baseline_trials) == 0 or baseline_trials[0].status != "completed"
    candidate_trials = [t for t in trials if not t.is_baseline]
    all_candidates_failed = len(candidate_trials) > 0 and all(t.status != "completed" for t in candidate_trials)

    if baseline_failed:
        overall_status = "failed"
        selection_reason = "Baseline estimator failed to fit; supervised experiment marked as failed."
        champion = None
    elif all_candidates_failed:
        overall_status = "failed"
        selection_reason = "All candidate supervised models failed during cross-validation; experiment marked as failed."
        champion = None
    elif champion is None:
        overall_status = "failed"
        selection_reason = "No eligible champion could be selected from completed trials."
    else:
        overall_status = "completed"

    # Refit champion on development rows and save
    if champion is not None:
        exp_dir = settings.experiments_dir / experiment_id
        exp_dir.mkdir(parents=True, exist_ok=True)
        try:
            refit_champion(
                champion=champion,
                df=df,
                view=view,
                manifest=manifest,
                prep_config=prep_config,
                seed=seed,
                experiment_dir=exp_dir,
            )
        except Exception as exc:
            selection_reason += f" [Refit warning: {exc}]"

    finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Build comparison key for compatible experiment ranking
    comparison_key_payload = {
        "dataset_id": dataset_id,
        "task": view.task.value,
        "target": view.target,
        "split_fingerprint": manifest.split_fingerprint,
        "primary_metric": primary_metric,
        "metric_version": METRIC_VERSION,
    }
    comparison_key = hashlib.sha256(
        json.dumps(comparison_key_payload, sort_keys=True).encode()
    ).hexdigest()

    return ExperimentSummary(
        id=experiment_id,
        project_id=project_id,
        dataset_id=dataset_id,
        split_id=manifest.split_id,
        task=view.task,
        name=experiment_name,
        status=overall_status,
        submission_token=submission_token,
        config_json=config_json,
        comparison_key=comparison_key,
        random_seed=seed,
        primary_metric=primary_metric,
        started_at=started_at,
        finished_at=finished_at,
        trials=trials,
        selected_trial_id=champion.trial_id if champion else None,
        selection_reason=selection_reason,
    )


def score_holdout(
    champion_pipeline: Any,
    holdout_df: pd.DataFrame,
    view: ModelingView,
    trial_id: str,
) -> Tuple[List[MetricRecord], Optional[List[List[int]]], Optional[List[str]]]:
    """
    Score the development-refit champion pipeline on sequestered holdout data.

    Returns:
        (metrics, confusion_matrix, class_labels)
    """
    feature_cols = view.numeric_features + view.categorical_features
    X_holdout = holdout_df[feature_cols]
    y_holdout = holdout_df[view.target]

    y_pred = champion_pipeline.predict(X_holdout)

    y_prob = None
    if hasattr(champion_pipeline, "predict_proba"):
        try:
            y_prob = champion_pipeline.predict_proba(X_holdout)
        except Exception:
            y_prob = None

    classes = getattr(champion_pipeline, "classes_", None)
    class_labels = [str(c) for c in classes] if classes is not None else None
    confusion_mat = None

    if view.task == TaskType.CLASSIFICATION:
        from sklearn.metrics import confusion_matrix

        if classes is not None:
            confusion_mat = confusion_matrix(y_holdout, y_pred, labels=classes).tolist()
        else:
            confusion_mat = confusion_matrix(y_holdout, y_pred).tolist()

        metrics = compute_classification_fold_metrics(
            y_true=y_holdout.to_numpy(),
            y_pred=np.array(y_pred),
            y_prob=y_prob,
            classes=classes,
            fold_index=-1,
            trial_id=trial_id,
        )
    else:
        metrics = compute_regression_fold_metrics(
            y_true=y_holdout.to_numpy(),
            y_pred=np.array(y_pred),
            fold_index=-1,
            trial_id=trial_id,
        )

    return metrics, confusion_mat, class_labels

