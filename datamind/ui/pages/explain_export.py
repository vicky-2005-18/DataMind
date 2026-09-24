"""Explain and export saved supervised experiments."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from datamind.services.experiments import ExperimentService
from datamind.services.export import ExportService
from datamind.ui.components import render_active_project_banner, render_header, render_service_error
from datamind.ui.navigation import NavigationContext


def render_explain_export_page() -> None:
    """Render saved-state explanations and evidence downloads."""
    render_header(
        title="Explain & Export",
        subtitle="Inspect a bounded development diagnostic and download stored experiment evidence",
    )
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
        figure = px.bar(
            chart,
            x="mean_importance",
            y="feature",
            orientation="h",
            error_x="std_importance",
            title="Development rows — original-feature permutation importance",
        )
        figure.add_vline(x=0)
        st.plotly_chart(figure, use_container_width=True)
        st.dataframe(chart, hide_index=True, use_container_width=True)
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
            use_container_width=True,
        )
    else:
        st.info("Holdout evaluation is not available because this experiment has not been finalized.")

    st.subheader("Evidence downloads")
    st.caption("All files are generated from saved records. Raw training data is excluded by default.")
    generators = [
        ("HTML report", export_service.generate_html_report, "text/html"),
        ("Markdown report", export_service.generate_markdown_report, "text/markdown"),
        ("Model ZIP", export_service.create_model_zip, "application/zip"),
        ("Experiment ZIP", export_service.create_experiment_zip, "application/zip"),
    ]
    columns = st.columns(4)
    for column, (label, generator, mime) in zip(columns, generators):
        with column:
            try:
                path = generator(experiment_id)
                st.download_button(
                    label,
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime=mime,
                    use_container_width=True,
                )
            except Exception as exc:
                render_service_error(exc)
