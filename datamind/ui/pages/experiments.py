"""Experiments page: Preprocessing configuration, algorithm selection, CV training, leaderboard, and holdout finalization."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from datamind.contracts import (
    AlgorithmConfig,
    PreprocessingConfig,
    ServiceError,
    TaskType,
)
from datamind.ml.registry import get_algorithms_for_task, get_baseline_for_task
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.ui.components import (
    render_active_project_banner,
    render_header,
    render_service_error,
)
from datamind.ui.navigation import NavigationContext


def render_experiments_page() -> None:
    """Render the Experiments page."""
    render_header(
        title="Supervised Experiments",
        subtitle="Configure preprocessing, evaluate models with leak-free cross-validation, finalize holdout, and manage trial history",
    )
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    if not active_project:
        return

    dataset_service = DatasetService()
    experiment_service = ExperimentService()

    datasets = dataset_service.list_datasets(active_project.id)
    if not datasets:
        st.info("No datasets available. Please load a dataset on the Datasets page first.")
        return

    ds_options = {d.id: f"{d.display_name} ({d.row_count:,} rows)" for d in datasets}
    active_ds_id = st.session_state.get("active_dataset_id")
    selected_idx = 0
    if active_ds_id and active_ds_id in ds_options:
        selected_idx = list(ds_options.keys()).index(active_ds_id)

    selected_dataset_id = st.selectbox(
        "Active Dataset",
        options=list(ds_options.keys()),
        index=selected_idx,
        format_func=lambda x: ds_options[x],
        key="exp_dataset_selector",
    )
    dataset = dataset_service.get_dataset(selected_dataset_id)
    if not dataset:
        return

    schema = dataset.get_schema()
    col_names = schema.column_names

    # ── 1. Model Protocol & Split ─────────────────────────────────────
    st.markdown("### 1. Model Protocol & Split")
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    with exp_col1:
        task = st.selectbox(
            "Task Type",
            options=[TaskType.CLASSIFICATION, TaskType.REGRESSION],
            format_func=lambda t: "Classification" if t == TaskType.CLASSIFICATION else "Regression",
            key="exp_task",
        )

    # Pick default target
    default_target_idx = len(col_names) - 1
    for i, col in enumerate(schema.columns):
        if col.name.lower() in ("target", "species", "label", "class"):
            default_target_idx = i
            break

    with exp_col2:
        target = st.selectbox(
            "Target Column",
            options=col_names,
            index=default_target_idx,
            key="exp_target",
        )
    with exp_col3:
        cv_folds = st.selectbox(
            "CV Folds",
            options=[5, 3],
            index=0,
            key="exp_cv_folds",
        )

    # Features
    features = [c for c in col_names if c != target]
    numeric_features = [c.name for c in schema.columns if c.name in features and c.inferred_type == "numeric"]
    categorical_features = [c for c in features if c not in numeric_features]

    # ── 2. Preprocessing Configuration ───────────────────────────────
    st.markdown("### 2. Preprocessing Configuration")
    st.caption("Transformers are fitted fold-locally inside each CV fold to guarantee zero data leakage.")
    prep_col1, prep_col2 = st.columns(2)
    with prep_col1:
        num_imputer = st.selectbox("Numeric Imputation Strategy", options=["median", "mean"], index=0)
    with prep_col2:
        num_scaler = st.selectbox("Numeric Feature Scaling", options=["standard", "minmax", "passthrough"], index=0)

    prep_config = PreprocessingConfig(
        numeric_imputer=num_imputer,
        numeric_scaler=num_scaler,
    )

    # ── 3. Algorithm Selection ────────────────────────────────────────
    st.markdown("### 3. Algorithm Selection")
    st.caption("Baseline model is mandatory and evaluated automatically. Select up to 4 additional algorithms to compete.")

    available_algos = get_algorithms_for_task(task)
    baseline_desc = get_baseline_for_task(task)
    candidate_algos = [a for a in available_algos if not a.is_baseline]

    st.info(f"📌 **Mandatory Baseline Included:** `{baseline_desc.display_name}` ({baseline_desc.algorithm_id})")

    algo_labels = {a.algorithm_id: f"{a.display_name} [{a.algorithm_id}]" for a in candidate_algos}
    default_selected = [a.algorithm_id for a in candidate_algos[:4]]

    selected_algo_ids = st.multiselect(
        "Choose Algorithms to Train",
        options=list(algo_labels.keys()),
        default=default_selected,
        format_func=lambda aid: algo_labels[aid],
        max_selections=4,
        key="exp_algo_multiselect",
    )

    exp_name = st.text_input(
        "Experiment Name",
        value=f"{dataset.display_name} - {task.value.capitalize()} Run",
        key="exp_name_input",
    )

    # ── Training Action ───────────────────────────────────────────────
    if st.button("🚀 Run Supervised Cross-Validation Experiment", type="primary", disabled=len(selected_algo_ids) == 0):
        try:
            with st.spinner("1/3 Validating modeling view and row policies..."):
                view = experiment_service.prepare_modeling_view(
                    dataset_id=dataset.id,
                    task=task,
                    target=target,
                    numeric_features=numeric_features,
                    categorical_features=categorical_features,
                )

            with st.spinner("2/3 Generating deterministic split & CV fold manifests..."):
                manifest = experiment_service.prepare_split(
                    dataset_id=dataset.id,
                    view=view,
                    test_fraction=0.20,
                    cv_folds=cv_folds,
                    random_seed=42,
                )

            algo_configs = [AlgorithmConfig(algorithm_id=aid) for aid in selected_algo_ids]

            with st.spinner(f"3/3 Fitting {len(algo_configs) + 1} algorithms across {cv_folds} identical folds..."):
                exp_summary = experiment_service.run_supervised_experiment(
                    experiment_name=exp_name.strip() or "Experiment",
                    project_id=active_project.id,
                    dataset_id=dataset.id,
                    view=view,
                    manifest=manifest,
                    algorithm_configs=algo_configs,
                    prep_config=prep_config,
                    seed=42,
                )

            st.session_state["latest_experiment"] = exp_summary
            st.success(f"✅ Experiment completed! Champion: **{exp_summary.selected_trial_id}**")
        except ServiceError as err:
            render_service_error(err)
        except Exception as exc:
            st.error(f"Experiment execution failed: {exc}")

    # ── CV Results Leaderboard ────────────────────────────────────────
    latest_exp = st.session_state.get("latest_experiment")
    if latest_exp and latest_exp.project_id == active_project.id:
        st.divider()
        st.subheader("🏆 Cross-Validation Results & Leaderboard")
        st.caption(f"Experiment: **{latest_exp.name}** • Primary Metric: `{latest_exp.primary_metric}` • Task: `{latest_exp.task.value}`")

        st.warning(
            "🔒 **Holdout Sequestered**: In accordance with the leakage prevention protocol, "
            "holdout test metrics are **strictly unavailable** during model exploration and CV training."
        )

        table_rows = []
        chart_data = []
        for trial in latest_exp.trials:
            is_champ = (trial.trial_id == latest_exp.selected_trial_id)
            cv_mean = trial.primary_cv_mean if trial.primary_cv_mean is not None else 0.0
            cv_std = trial.primary_cv_std if trial.primary_cv_std is not None else 0.0

            table_rows.append({
                "Algorithm": trial.algorithm_id + (" (Baseline)" if trial.is_baseline else ""),
                "Status": trial.status.upper(),
                f"CV {latest_exp.primary_metric} (Mean)": f"{cv_mean:.4f}" if trial.primary_cv_mean is not None else "N/A",
                "Fold Std (ddof=0)": f"±{cv_std:.4f}" if trial.primary_cv_std is not None else "N/A",
                "Fit Duration": f"{trial.fit_duration_seconds:.3f}s",
                "Outcome": "★ CHAMPION" if is_champ else ("Baseline" if trial.is_baseline else ""),
            })

            if trial.status == "completed" and trial.primary_cv_mean is not None:
                chart_data.append({
                    "Algorithm": trial.algorithm_id + (" (Baseline)" if trial.is_baseline else ""),
                    "CV Score": cv_mean,
                    "Fold Variation": cv_std,
                    "Is Champion": "Champion" if is_champ else "Competitor",
                })

        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        if chart_data:
            chart_df = pd.DataFrame(chart_data)
            fig = px.bar(
                chart_df,
                x="Algorithm",
                y="CV Score",
                error_y="Fold Variation",
                color="Is Champion",
                title=f"Cross-Validation Comparison ({latest_exp.primary_metric}) with Fold Variation",
                color_discrete_map={"Champion": "#00CC96", "Competitor": "#636EFA"},
            )
            st.plotly_chart(fig, use_container_width=True)

        st.info(f"**Selection Audit**: {latest_exp.selection_reason}")

    # ── Finalize Holdout (M3) ─────────────────────────────────────────
    st.divider()
    st.subheader("🔓 Finalize Holdout Evaluation")
    st.caption(
        "Once you are satisfied with CV exploration, explicitly finalize the champion model. "
        "This is a one-time irreversible action — the model is scored against the sequestered "
        "holdout partition and the result is permanently recorded."
    )

    all_experiments = experiment_service.list_experiments(active_project.id)
    completed_exps = [e for e in all_experiments if e.status == "completed" and e.selected_trial_id]

    if not completed_exps:
        st.info("No completed experiments with a champion model found. Run an experiment above first.")
    else:
        exp_options = {e.id: f"{e.name} [{e.id[:8]}] — Champion: {e.selected_trial_id[:8]}" for e in completed_exps}
        finalize_exp_id = st.selectbox(
            "Select Experiment to Finalize",
            options=list(exp_options.keys()),
            format_func=lambda eid: exp_options[eid],
            key="finalize_exp_selector",
        )

        # Check if already finalized
        existing_eval = experiment_service.get_evaluation(finalize_exp_id)
        if existing_eval is not None:
            st.success(f"✅ This experiment was already finalized on `{existing_eval.created_at}`.")
            if existing_eval.holdout_previously_exposed:
                st.warning(
                    "⚠️ **Holdout Previously Exposed**: This holdout split was evaluated in a prior "
                    "experiment. The holdout test set is no longer strictly unseen."
                )
            _render_evaluation_results(existing_eval)
        else:
            st.warning(
                "⚠️ **Irreversible Action**: Finalizing will expose the champion to the holdout "
                "partition. This cannot be undone."
            )
            if st.button("🔓 Finalize Holdout Evaluation", key="finalize_btn", type="primary"):
                try:
                    with st.spinner("Scoring champion against sequestered holdout rows..."):
                        evaluation = experiment_service.finalize_experiment(finalize_exp_id)
                    st.success("✅ Holdout evaluation complete and permanently recorded.")
                    if evaluation.holdout_previously_exposed:
                        st.warning(
                            "⚠️ **Holdout Previously Exposed**: Another experiment on the same "
                            "split was finalized before this one."
                        )
                    _render_evaluation_results(evaluation)
                except ServiceError as err:
                    render_service_error(err)
                except Exception as exc:
                    st.error(f"Finalization failed: {exc}")

    # ── Trial History (M3: persistence restart) ───────────────────────
    st.divider()
    st.subheader("📋 Experiment History")
    st.caption("All experiments for this project are persisted in SQLite and survive server restarts.")
    if all_experiments:
        history_rows = []
        for e in all_experiments:
            eval_rec = experiment_service.get_evaluation(e.id)
            finalized = "✅ Yes" if eval_rec is not None else "—"
            history_rows.append({
                "ID": e.id[:8],
                "Name": e.name,
                "Task": e.task.value,
                "Status": e.status,
                "Champion": (e.selected_trial_id or "—")[:8] if e.selected_trial_id else "—",
                "Primary Metric": e.primary_metric,
                "Started": e.started_at[:19].replace("T", " "),
                "Finalized": finalized,
            })
        st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
    else:
        st.info("No experiments yet. Run one above to begin.")


def _render_evaluation_results(evaluation) -> None:
    """Display holdout evaluation metrics and confusion matrix."""
    if not evaluation.metrics:
        st.info("No holdout metrics recorded.")
        return

    st.markdown("#### Holdout Evaluation Metrics")
    metric_rows = []
    for m in evaluation.metrics:
        metric_rows.append({
            "Metric": m.name,
            "Value": f"{m.value:.6f}" if m.value is not None else "N/A",
            "Direction": m.direction.value,
        })
    st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)

    if evaluation.confusion_matrix and evaluation.class_labels:
        st.markdown("#### Confusion Matrix")
        cm_df = pd.DataFrame(
            evaluation.confusion_matrix,
            index=[f"True: {c}" for c in evaluation.class_labels],
            columns=[f"Pred: {c}" for c in evaluation.class_labels],
        )
        st.dataframe(cm_df, use_container_width=True)
