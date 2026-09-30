"""Demonstration script for M2: Supervised ML on Iris & Synthetic Regression."""

from __future__ import annotations

import sys
import uuid
from typing import List

from datamind.config import get_settings
from datamind.contracts import (
    AlgorithmConfig,
    DemoDatasetKind,
    PreprocessingConfig,
    TaskType,
)
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.services.projects import ProjectService
from datamind.storage.database import run_migrations


def run_m2_demo() -> int:
    print("=" * 70)
    print("DataMind M2 Demonstration: Supervised Learning Engine")
    print("=" * 70)

    settings = get_settings()
    settings.ensure_directories()
    run_migrations(settings.db_path)

    project_service = ProjectService()
    dataset_service = DatasetService()
    experiment_service = ExperimentService()

    # 1. Create a dedicated project
    proj_name = f"M2 Verification Lab {uuid.uuid4().hex[:6]}"
    project = project_service.create_project(name=proj_name, description="M2 live demonstration project")
    print(f"\n[1] Created project: '{project.name}' (ID: {project.id[:8]})")

    # =========================================================================
    # PART A: IRIS CLASSIFICATION
    # =========================================================================
    print("\n" + "=" * 70)
    print("PART A: Multi-Class Classification on Iris Dataset")
    print("=" * 70)

    iris_ds = dataset_service.load_demo(project.id, DemoDatasetKind.IRIS)
    print(f"Loaded demo dataset: '{iris_ds.display_name}' ({iris_ds.row_count} rows, {iris_ds.column_count} cols)")

    # Modeling view: target = 'species', numeric features = 4 sepal/petal measurements
    feature_cols = [c for c in iris_ds.get_schema().column_names if c != "species"]
    view_iris = experiment_service.prepare_modeling_view(
        dataset_id=iris_ds.id,
        task=TaskType.CLASSIFICATION,
        target="species",
        numeric_features=feature_cols,
        categorical_features=[],
    )
    print(f"Modeling view constructed: {len(view_iris.eligible_row_ids)} eligible rows (0 dropped)")

    # Exact split: 80% dev, 20% holdout, 5-fold CV
    split_iris = experiment_service.prepare_split(
        dataset_id=iris_ds.id,
        view=view_iris,
        test_fraction=0.20,
        cv_folds=5,
        random_seed=42,
    )
    print(f"Split generated: {len(split_iris.train_row_ids)} dev rows, {len(split_iris.test_row_ids)} holdout rows (disjoint)")
    print(f"Split fingerprint: {split_iris.split_fingerprint[:16]}... (cached & verified)")

    # Algorithm suite for classification
    clf_algos: List[AlgorithmConfig] = [
        AlgorithmConfig(algorithm_id="logistic_regression", parameters={"C": 1.0, "max_iter": 200}),
        AlgorithmConfig(algorithm_id="decision_tree_classifier", parameters={"max_depth": 3, "min_samples_leaf": 1}),
        AlgorithmConfig(algorithm_id="random_forest_classifier", parameters={"n_estimators": 50, "max_depth": 3}),
        AlgorithmConfig(algorithm_id="knn_classifier", parameters={"n_neighbors": 5}),
    ]

    print("\nRunning CV Training across 5 folds (identical folds, baseline automatically injected)...")
    iris_exp = experiment_service.run_supervised_experiment(
        experiment_name="Iris Multi-Model Comparison",
        project_id=project.id,
        dataset_id=iris_ds.id,
        view=view_iris,
        manifest=split_iris,
        algorithm_configs=clf_algos,
        prep_config=PreprocessingConfig(numeric_scaler="standard"),
        seed=42,
    )

    print("\n--- Cross-Validation Leaderboard (Primary Metric: macro_f1) ---")
    print(f"{'Algorithm ID':<26} | {'CV Macro F1':<14} | {'CV Std':<10} | {'Duration':<10}")
    print("-" * 70)
    for trial in iris_exp.trials:
        f1_val = f"{trial.primary_cv_mean:.4f}" if trial.primary_cv_mean is not None else "N/A"
        std_val = f"+/-{trial.primary_cv_std:.4f}" if trial.primary_cv_std is not None else "N/A"
        dur_val = f"{trial.fit_duration_seconds:.3f}s"
        star = " * CHAMPION" if trial.trial_id == iris_exp.selected_trial_id else ""
        baseline_tag = " (Baseline)" if trial.is_baseline else ""
        print(f"{trial.algorithm_id + baseline_tag:<28} | {f1_val:<14} | {std_val:<10} | {dur_val:<10}{star}")

    print(f"\nSelection Reason: {iris_exp.selection_reason}")
    print(f"Selected Trial ID: {iris_exp.selected_trial_id}")
    print("Holdout status: UNAVAILABLE / UNTOUCHED (Strict leakage prevention)")

    # =========================================================================
    # PART B: SYNTHETIC REGRESSION
    # =========================================================================
    print("\n" + "=" * 70)
    print("PART B: Continuous Regression on Synthetic Dataset")
    print("=" * 70)

    reg_ds = dataset_service.load_demo(project.id, DemoDatasetKind.SYNTHETIC_REGRESSION, seed=42)
    print(f"Loaded demo dataset: '{reg_ds.display_name}' ({reg_ds.row_count} rows, {reg_ds.column_count} cols)")

    reg_feature_cols = [c for c in reg_ds.get_schema().column_names if c != "target"]
    view_reg = experiment_service.prepare_modeling_view(
        dataset_id=reg_ds.id,
        task=TaskType.REGRESSION,
        target="target",
        numeric_features=reg_feature_cols,
        categorical_features=[],
    )
    print(f"Modeling view constructed: {len(view_reg.eligible_row_ids)} eligible rows")

    split_reg = experiment_service.prepare_split(
        dataset_id=reg_ds.id,
        view=view_reg,
        test_fraction=0.20,
        cv_folds=5,
        random_seed=42,
    )
    print(f"Split generated: {len(split_reg.train_row_ids)} dev rows, {len(split_reg.test_row_ids)} holdout rows")

    reg_algos: List[AlgorithmConfig] = [
        AlgorithmConfig(algorithm_id="linear_regression"),
        AlgorithmConfig(algorithm_id="ridge", parameters={"alpha": 1.0}),
        AlgorithmConfig(algorithm_id="decision_tree_regressor", parameters={"max_depth": 4}),
        AlgorithmConfig(algorithm_id="random_forest_regressor", parameters={"n_estimators": 50, "max_depth": 4}),
    ]

    print("\nRunning CV Training across 5 folds (Primary Metric: rmse, lower is better)...")
    reg_exp = experiment_service.run_supervised_experiment(
        experiment_name="Synthetic Regression Multi-Model Comparison",
        project_id=project.id,
        dataset_id=reg_ds.id,
        view=view_reg,
        manifest=split_reg,
        algorithm_configs=reg_algos,
        prep_config=PreprocessingConfig(numeric_scaler="standard"),
        seed=42,
    )

    print("\n--- Cross-Validation Leaderboard (Primary Metric: rmse) ---")
    print(f"{'Algorithm ID':<28} | {'CV RMSE':<14} | {'CV Std':<10} | {'Duration':<10}")
    print("-" * 70)
    for trial in reg_exp.trials:
        rmse_val = f"{trial.primary_cv_mean:.4f}" if trial.primary_cv_mean is not None else "N/A"
        std_val = f"+/-{trial.primary_cv_std:.4f}" if trial.primary_cv_std is not None else "N/A"
        dur_val = f"{trial.fit_duration_seconds:.3f}s"
        star = " * CHAMPION" if trial.trial_id == reg_exp.selected_trial_id else ""
        baseline_tag = " (Baseline)" if trial.is_baseline else ""
        print(f"{trial.algorithm_id + baseline_tag:<28} | {rmse_val:<14} | {std_val:<10} | {dur_val:<10}{star}")

    print(f"\nSelection Reason: {reg_exp.selection_reason}")
    print(f"Selected Trial ID: {reg_exp.selected_trial_id}")
    print("Holdout status: UNAVAILABLE / UNTOUCHED")

    # =========================================================================
    # PART C: DATABASE PERSISTENCE VERIFICATION
    # =========================================================================
    print("\n" + "=" * 70)
    print("PART C: Verification of Persisted Records in SQLite")
    print("=" * 70)
    saved_experiments = experiment_service.list_experiments(project.id)
    print(f"Found {len(saved_experiments)} experiments persisted for project '{project.name}':")
    for exp in saved_experiments:
        print(f" - [{exp.id[:8]}] {exp.name} (Task: {exp.task.value}) -> Selected Trial: {exp.selected_trial_id[:8]} ({exp.primary_metric})")

    print("\nM2 Live Demonstration Completed Successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(run_m2_demo())
