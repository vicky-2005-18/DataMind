"""Explain and export saved supervised experiments."""

from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from datamind.services.experiments import ExperimentService
from datamind.services.export import ExportService
from datamind.ui.components import (
    pill_html,
    render_active_project_banner,
    render_header,
    render_service_error,
    render_workflow_stepper,
    style_plotly_figure,
)
from datamind.ui.navigation import NavigationContext


def render_explain_export_page() -> None:
    """Render saved-state explanations and evidence downloads."""
    render_header(
        title="Explain & Export",
        subtitle="Inspect a bounded development diagnostic and download stored experiment evidence",
    )
    render_workflow_stepper("Deliver")
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)
    if not active_project:
        return

    experiment_service = ExperimentService()
    experiments = [
        experiment
        for experiment in experiment_service.list_experiments(active_project.id)
        if experiment.task.value != "clustering" and experiment.selected_trial_id
    ]
    if not experiments:
        st.info("Run a successful supervised experiment before opening explanations and exports.")
        return

    labels = {experiment.id: f"{experiment.name} [{experiment.id[:8]}]" for experiment in experiments}
    experiment_id = st.selectbox(
        "Saved experiment",
        options=list(labels),
        format_func=lambda value: labels[value],
    )
    experiment = experiment_service.get_experiment(experiment_id)
    export_service = ExportService(experiment_service=experiment_service)

    st.subheader(experiment.name)
    st.caption(
        f"Task: {experiment.task.value} • primary CV metric: {experiment.primary_metric} • saved seed: {experiment.random_seed}"
    )
    try:
        records = export_service.compute_importance(experiment_id)
        chart = pd.DataFrame(records).sort_values("mean_importance")
        # Color-code direction: emerald for positive impact, coral for negative
        chart["impact"] = chart["mean_importance"].map(
            lambda value: "increases score" if value > 0 else "decreases score"
        )
        figure = px.bar(
            chart,
            x="mean_importance",
            y="feature",
            orientation="h",
            error_x="std_importance",
            color="impact",
            color_discrete_map={
                "increases score": "#10b981",
                "decreases score": "#f43f5e",
            },
            title="Development rows — original-feature permutation importance",
        )
        figure.add_vline(x=0, line_color="#475569")
        figure = style_plotly_figure(figure)
        st.plotly_chart(figure, width='stretch')
        st.dataframe(chart, hide_index=True, width='stretch')

        # Natural-language summary of the top driving factors
        top_drivers = chart.reindex(chart["mean_importance"].abs().sort_values(ascending=False).index).head(3)
        driver_phrases = []
        for _, row in top_drivers.iterrows():
            direction = "raises" if row["mean_importance"] > 0 else "lowers"
            driver_phrases.append(
                f"<strong>{escape(str(row['feature']))}</strong> "
                f"({direction} development score by {row['mean_importance']:.4f} on average)"
            )
        drivers_html = " • ".join(driver_phrases)
        st.markdown(
            f"<p style='font-size:0.9rem; color:var(--dm-text);'>"
            f"Top development-set drivers: {drivers_html}</p>",
            unsafe_allow_html=True,
        )

        st.info(
            "Development-set diagnostic only: this is not independent evaluation and not causal evidence. "
            "Correlated features can obscure importance, and negative values are legitimate."
        )
    except Exception as exc:
        render_service_error(exc)

    evaluation = experiment_service.get_evaluation(experiment_id)
    if evaluation:
        st.subheader("Holdout — finalized")
        st.caption(
            f"Holdout previously exposed: {'Yes' if evaluation.holdout_previously_exposed else 'No'}"
        )
        st.dataframe(
            pd.DataFrame([metric.model_dump(mode="json") for metric in evaluation.metrics]),
            hide_index=True,
            width='stretch',
        )
    else:
        st.info("Holdout evaluation is not available because this experiment has not been finalized.")

    st.subheader("Evidence downloads")
    st.caption("All files are generated from saved records. Raw training data is excluded by default.")

    report_generators = [
        ("HTML report", "generate_html_report", "text/html"),
        ("Markdown report", "generate_markdown_report", "text/markdown"),
    ]
    archive_generators = [
        ("Model ZIP", "create_model_zip", "application/zip"),
        ("Experiment ZIP", "create_experiment_zip", "application/zip"),
    ]

    capsule_groups = [
        (
            "Reports",
            pill_html("Human-readable", "primary"),
            "Narrative summaries generated from persisted experiment records.",
            report_generators,
        ),
        (
            "Reproducibility archives",
            pill_html("Artifacts", "cyan"),
            "Bundles with the champion pipeline, schema, and evidence for re-running offline.",
            archive_generators,
        ),
    ]

    for group_title, kicker, caption, generators in capsule_groups:
        with st.container(border=True):
            st.markdown(kicker, unsafe_allow_html=True)
            st.markdown(f"**{group_title}**")
            st.caption(caption)
            columns = st.columns(len(generators))
            for column, (label, method_name, mime) in zip(columns, generators):
                with column:
                    try:
                        generator = getattr(export_service, method_name)
                        path = generator(experiment_id)
                        st.download_button(
                            label,
                            data=path.read_bytes(),
                            file_name=path.name,
                            mime=mime,
                            key=f"export_{method_name}_{experiment_id[:8]}",
                            width='stretch',
                        )
                    except Exception as exc:
                        render_service_error(exc)
