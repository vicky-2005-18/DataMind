"""Compare page: compatible multi-experiment leaderboard with strict cohort validation (M3)."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from datamind.contracts import ServiceError
from datamind.services.comparison import ComparisonService
from datamind.services.experiments import ExperimentService
from datamind.ui.components import (
    render_active_project_banner,
    render_header,
    render_service_error,
)
from datamind.ui.navigation import NavigationContext


def render_compare_page() -> None:
    """Render the Compare page."""
    render_header(
        title="Experiment Comparison",
        subtitle="Compare compatible runs that share the same dataset, task, target, and split manifest",
    )
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    if not active_project:
        return

    experiment_service = ExperimentService()
    comparison_service = ComparisonService(experiment_service=experiment_service)

    all_experiments = experiment_service.list_experiments(active_project.id)
    completed_exps = [
        e
        for e in all_experiments
        if e.status == "completed" and e.selected_trial_id and e.task.value != "clustering"
    ]

    if len(completed_exps) < 2:
        st.info(
            "At least **2 completed experiments** with a champion model are required for comparison. "
            "Run more experiments on the **Supervised Experiments** page."
        )
        return

    exp_options = {
        e.id: f"{e.name} [{e.id[:8]}] — {e.task.value} — {e.primary_metric}"
        for e in completed_exps
    }

    st.markdown("### Select Experiments to Compare")
    st.caption(
        "DataMind enforces strict cohort compatibility: only experiments sharing the identical "
        "dataset, task, target column, split fingerprint, and primary metric can be compared."
    )

    selected_ids = st.multiselect(
        "Choose 2 or more completed experiments",
        options=list(exp_options.keys()),
        format_func=lambda eid: exp_options[eid],
        key="compare_exp_multiselect",
    )

    if len(selected_ids) < 2:
        st.info("Select at least **2** experiments above to enable comparison.")
        return

    if st.button("📊 Compare Selected Experiments", type="primary", key="compare_btn"):
        try:
            result = comparison_service.compare(selected_ids)
            st.session_state["comparison_result"] = result
        except ServiceError as err:
            render_service_error(err)
        except Exception as exc:
            st.error(f"Comparison failed: {exc}")

    result = st.session_state.get("comparison_result")
    if result is None:
        return

    # Verify the result still corresponds to the current selection
    if set(result.candidate_experiment_ids) != set(selected_ids):
        st.session_state.pop("comparison_result", None)
        st.info("Selection changed — click Compare again.")
        return

    st.divider()
    st.subheader(f"📈 Comparison Leaderboard — Primary Metric: `{result.primary_metric}`")

    # Build leaderboard dataframe
    leaderboard_rows = []
    for row in result.table_rows:
        leaderboard_rows.append({
            "Experiment": f"{row['experiment_name']} [{row['experiment_id'][:8]}]",
            "Champion Algorithm": row["champion_algorithm"],
            "CV Mean": f"{row['cv_mean']:.6f}" if row["cv_mean"] is not None else "N/A",
            "CV Std": f"±{row['cv_std']:.4f}" if row["cv_std"] is not None else "N/A",
            "Trials": row["trials_count"],
            "Total Fit (s)": f"{row['total_fit_duration']:.2f}",
            "Started": str(row["started_at"])[:19].replace("T", " "),
        })

    st.dataframe(pd.DataFrame(leaderboard_rows), use_container_width=True, hide_index=True)

    # Chart
    if result.table_rows:
        chart_df = pd.DataFrame([
            {
                "Experiment": f"{r['experiment_name']} [{r['experiment_id'][:8]}]",
                "CV Mean": r["cv_mean"],
                "CV Std": r["cv_std"] if r["cv_std"] is not None else 0.0,
            }
            for r in result.table_rows
            if r["cv_mean"] is not None
        ])
        if not chart_df.empty:
            fig = px.bar(
                chart_df,
                x="Experiment",
                y="CV Mean",
                error_y="CV Std",
                title=f"CV {result.primary_metric} Comparison Across Compatible Experiments",
                color="Experiment",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Config differences
    if result.config_differences:
        st.markdown("### ⚙️ Configuration Differences")
        diff_rows = []
        for d in result.config_differences:
            diff_rows.append({
                "Experiment": f"{d['experiment_name']} [{d['experiment_id'][:8]}]",
                "Algorithms": ", ".join(d.get("algorithms", [])),
                "Seed": d.get("seed"),
                "Imputer": d.get("prep_config", {}).get("numeric_imputer", "—"),
                "Scaler": d.get("prep_config", {}).get("numeric_scaler", "—"),
            })
        st.dataframe(pd.DataFrame(diff_rows), use_container_width=True, hide_index=True)

    st.success(
        "✅ All experiments above share the same dataset, task, target, and split fingerprint. "
        "This is a valid, unbiased comparison."
    )
