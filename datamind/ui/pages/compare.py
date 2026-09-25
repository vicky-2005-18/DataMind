"""Compare page: compatible multi-experiment leaderboard with strict cohort validation."""

from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from datamind.contracts import MetricScope, ServiceError, TaskType
from datamind.services.comparison import ComparisonService
from datamind.services.experiments import ExperimentService
from datamind.ui.components import (
    render_active_project_banner,
    render_header,
    render_rank_medal,
    render_service_error,
    render_workflow_stepper,
    style_plotly_figure,
)
from datamind.ui.navigation import NavigationContext

# Metrics where a lower CV value is better; everything else is maximized.
MINIMIZED_METRICS = {"rmse", "mae"}


def _is_minimized(primary_metric: str) -> bool:
    return primary_metric.lower() in MINIMIZED_METRICS


def _best_row(table_rows, primary_metric: str):
    """Return the best row honoring metric direction, or None."""
    usable = [row for row in table_rows if row.get("cv_mean") is not None]
    if not usable:
        return None
    if _is_minimized(primary_metric):
        return min(usable, key=lambda r: r["cv_mean"])
    return max(usable, key=lambda r: r["cv_mean"])


def _ranked_rows(table_rows, primary_metric: str):
    """Return rows ordered best-first honoring metric direction."""
    usable = [row for row in table_rows if row.get("cv_mean") is not None]
    if _is_minimized(primary_metric):
        return sorted(usable, key=lambda r: r["cv_mean"])
    return sorted(usable, key=lambda r: r["cv_mean"], reverse=True)


def render_compare_page() -> None:
    """Render the Compare page."""
    render_header(
        title="Experiment Comparison",
        subtitle="Compare compatible runs that share the same dataset, task, target, and split manifest",
    )
    render_workflow_stepper("Model")
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

    if st.button("Compare Selected Experiments", type="primary", key="compare_btn"):
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

    # Cohort badge banner
    st.markdown(
        f"""
        <div style="background: var(--dm-surface-primary); border: 1px solid var(--dm-border); border-radius: var(--dm-radius-md); padding: 0.75rem 1rem; margin-bottom: 1.25rem; display: flex; gap: 1.2rem; flex-wrap: wrap;">
            <div><span style="color: var(--dm-muted); font-size: 0.75rem; text-transform: uppercase; font-weight: 750;">Dataset:</span> <strong style="color: var(--dm-text);">{escape(result.dataset_name)}</strong></div>
            <div><span style="color: var(--dm-muted); font-size: 0.75rem; text-transform: uppercase; font-weight: 750;">Task:</span> <span class="dm-pill dm-pill-primary">{escape(result.task)}</span></div>
            <div><span style="color: var(--dm-muted); font-size: 0.75rem; text-transform: uppercase; font-weight: 750;">Target:</span> <code>{escape(result.target_column)}</code></div>
            <div><span style="color: var(--dm-muted); font-size: 0.75rem; text-transform: uppercase; font-weight: 750;">Primary Metric:</span> <strong style="color: var(--dm-primary);">{escape(result.primary_metric)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Highlight top champion (metric-direction aware)
    best_row = _best_row(result.table_rows, result.primary_metric)
    if best_row is not None:
        direction_note = (
            "lower is better" if _is_minimized(result.primary_metric) else "higher is better"
        )
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(6, 182, 212, 0.05));
                        border: 1px solid rgba(99, 102, 241, 0.3); border-radius: var(--dm-radius-md); padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                    <div>
                        <span class="dm-pill dm-pill-success" style="font-weight: 800; font-size: 0.75rem;">LEADER / CHAMPION</span>
                        <h3 style="margin: 0.35rem 0 0.15rem; color: var(--dm-text); font-size: 1.2rem;">{escape(best_row['experiment_name'])}</h3>
                        <span style="color: var(--dm-muted); font-size: 0.85rem;">Algorithm: <strong>{escape(best_row['champion_algorithm'])}</strong></span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--dm-muted); font-weight: 750; text-transform: uppercase;">CV MEAN ({escape(result.primary_metric)} — {direction_note})</div>
                        <div style="font-family: var(--dm-font-mono); font-size: 1.8rem; font-weight: 800; color: var(--dm-primary);">{best_row['cv_mean']:.5f}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Comparison Leaderboard")

    # Medal podium for the top-3 ranked runs (metric-direction aware)
    ranked = _ranked_rows(result.table_rows, result.primary_metric)
    if ranked:
        podium_html = " ".join(
            f"<div style='display:flex; align-items:center; gap:0.45rem; margin:0.2rem 0;'>"
            f"{render_rank_medal(rank)}<strong style='color:var(--dm-text-strong);'>"
            f"{escape(row['experiment_name'])}</strong>"
            f"<span style='color:var(--dm-text-dim); font-family:var(--dm-font-mono);'>"
            f"{row['cv_mean']:.4f}</span></div>"
            for rank, row in enumerate(ranked[:3], start=1)
        )
        st.markdown(podium_html, unsafe_allow_html=True)

    # Build leaderboard dataframe with real ranking
    rank_of = {row["experiment_id"]: rank for rank, row in enumerate(ranked, start=1)}
    leaderboard_rows = []
    for row in result.table_rows:
        leaderboard_rows.append({
            "Rank": rank_of.get(row["experiment_id"], "—"),
            "Experiment": f"{row['experiment_name']} [{row['experiment_id'][:8]}]",
            "Champion Algorithm": row["champion_algorithm"],
            "CV Mean": f"{row['cv_mean']:.6f}" if row["cv_mean"] is not None else "N/A",
            "CV Std": f"±{row['cv_std']:.4f}" if row["cv_std"] is not None else "N/A",
            "Trials": row["trials_count"],
            "Total Fit (s)": f"{row['total_fit_duration']:.2f}",
            "Started": str(row["started_at"])[:19].replace("T", " "),
        })

    st.dataframe(pd.DataFrame(leaderboard_rows), width='stretch', hide_index=True)
    st.caption(
        "Ranking direction follows the primary metric: rmse and mae rank lower-is-better; all other "
        "metrics rank higher-is-better. The table remains fully sortable."
    )

    # Chart with direction-correct ordering: best run at the top
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
            chart_df = chart_df.sort_values("CV Mean", ascending=_is_minimized(result.primary_metric))
            fig = px.bar(
                chart_df,
                x="CV Mean",
                y="Experiment",
                error_x="CV Std",
                orientation="h",
                title=f"{result.primary_metric} Comparison (Best Run on Top)",
                labels={"CV Mean": f"{result.primary_metric} (CV Mean)", "Experiment": "Run"},
                color="CV Mean",
                color_continuous_scale="Purples",
            )
            fig = style_plotly_figure(fig)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width='stretch')
            direction_note = (
                "lower is better" if _is_minimized(result.primary_metric) else "higher is better"
            )
            st.caption(
                f"Experiments sorted best-first ({direction_note}). Error bars show CV standard deviation."
            )

    # Multi-metric radar of champion trials (classification cohorts, all metrics on [0,1])
    _render_champion_radar(experiment_service, result, selected_ids)

    # Config differences
    if result.config_differences:
        st.markdown("### Configuration Differences")
        diff_rows = []
        for d in result.config_differences:
            diff_rows.append({
                "Experiment": f"{d['experiment_name']} [{d['experiment_id'][:8]}]",
                "Algorithms": ", ".join(d.get("algorithms", [])),
                "Seed": d.get("seed"),
                "Imputer": d.get("prep_config", {}).get("numeric_imputer", "—"),
                "Scaler": d.get("prep_config", {}).get("numeric_scaler", "—"),
            })
        st.dataframe(pd.DataFrame(diff_rows), width='stretch', hide_index=True)

    st.success(
        "All experiments above share the same dataset, task, target, and split fingerprint. "
        "This is a valid, unbiased comparison."
    )


def _render_champion_radar(experiment_service: ExperimentService, result, selected_ids) -> None:
    """Render a multi-metric radar of champion trials from stored per-fold metrics.

    Only rendered for classification cohorts where every metric lies on [0, 1]; a
    regression radar would mix incommensurable scales (rmse vs r2), so it is skipped
    honestly instead of faked.
    """
    if result.task != TaskType.CLASSIFICATION.value:
        st.caption(
            "Multi-metric radar is only rendered for classification cohorts. Regression metrics "
            "(rmse, mae, r2) live on incommensurable scales, so an overlay would be misleading."
        )
        return

    series = {}
    for experiment_id in selected_ids:
        experiment = experiment_service.get_experiment(experiment_id)
        if not experiment or not experiment.selected_trial_id:
            continue
        champion = next(
            (t for t in experiment.trials if t.trial_id == experiment.selected_trial_id), None
        )
        if champion is None:
            continue
        per_metric: dict[str, float] = {}
        for record in champion.metrics:
            if record.scope != MetricScope.CV_FOLD:
                continue
            per_metric.setdefault(record.name, 0.0)
            per_metric[record.name] += record.value
        fold_counts: dict[str, int] = {}
        for record in champion.metrics:
            if record.scope == MetricScope.CV_FOLD:
                fold_counts[record.name] = fold_counts.get(record.name, 0) + 1
        means = {
            name: total / fold_counts.get(name, 1) for name, total in per_metric.items()
        }
        if means:
            series[f"{experiment.name} [{experiment.id[:8]}]"] = means

    if not series:
        st.caption("No stored per-fold metrics are available for a champion radar in this cohort.")
        return

    metric_names = sorted({name for means in series.values() for name in means})
    radar_df = pd.DataFrame(
        [
            {"Metric": name, "CV Mean": means.get(name), "Experiment": label}
            for label, means in series.items()
            for name in metric_names
        ]
    )
    fig = px.line_polar(
        radar_df,
        r="CV Mean",
        theta="Metric",
        line_close=True,
        color="Experiment",
        title="Champion Trial Multi-Metric Profile (Mean per CV Fold)",
        range_r=[0.0, 1.0],
    )
    fig = style_plotly_figure(fig)
    st.plotly_chart(fig, width='stretch')
    st.caption(
        "Each axis is the mean of the champion trial's per-fold metric on development rows. "
        "Per-trial predicted probabilities are not persisted, so ROC overlays are unavailable "
        "rather than approximated."
    )
