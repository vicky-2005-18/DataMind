"""Home page: workspace overview, project creation, and project selection.

Phase 3: hero bento with live lab stats, dataset health card, and activity timeline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape

import streamlit as st

from datamind.contracts import DemoDatasetKind, ServiceError
from datamind.services.datasets import DatasetService
from datamind.services.experiments import ExperimentService
from datamind.services.projects import ProjectService
from datamind.ui.components import (
    pill_html,
    render_active_project_banner,
    render_activity_timeline,
    render_bento_grid,
    render_header,
    render_hero_stats,
    render_service_error,
    render_workflow_stepper,
)
from datamind.ui.navigation import NavigationContext

QUICK_START_DEMOS = [
    (DemoDatasetKind.IRIS, "Iris Classification Demo"),
    (DemoDatasetKind.SYNTHETIC_REGRESSION, "Synthetic Regression Demo"),
    (DemoDatasetKind.SYNTHETIC_BLOBS, "Synthetic Blobs Clustering Demo"),
]


def _relative_time(iso_timestamp: str) -> str:
    """Return a short human-readable delta for ISO timestamps."""
    try:
        stamp = datetime.fromisoformat(iso_timestamp)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - stamp
        seconds = int(delta.total_seconds())
        if seconds < 0:
            return "just now"
        if seconds < 60:
            return f"{seconds}s ago"
        if seconds < 3600:
            return f"{seconds // 60}m ago"
        if seconds < 86400:
            return f"{seconds // 3600}h ago"
        return f"{seconds // 86400}d ago"
    except (ValueError, TypeError):
        return iso_timestamp[:10]


def _load_demo(kind: DemoDatasetKind, project_id: str) -> None:
    try:
        new_dataset = DatasetService().load_demo(
            project_id=project_id,
            demo_kind=kind,
        )
        NavigationContext.set_active_dataset(new_dataset.id)
        st.success(f"Loaded **{new_dataset.display_name}** successfully!")
        st.rerun()
    except Exception as exc:
        render_service_error(exc)


def render_home_page() -> None:
    """Render the Home page for DataMind."""
    render_header(
        title="Welcome to DataMind",
        subtitle="Train, compare, and deploy ML models in a reproducible local workspace",
    )
    render_workflow_stepper("Workspace")

    service = ProjectService()
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    st.subheader("Active Experimentation Lab")
    if not active_project:
        st.info("Create or select a project to begin building a reproducible workspace.")
    else:
        _render_lab_bento(active_project)

    st.write("")
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("New Project")
        st.caption("Start a reproducible ML workspace with isolated artifacts")

        with st.form("create_project_form", clear_on_submit=True):
            name = st.text_input(
                "Project Name",
                placeholder="e.g. Customer Churn Prediction",
                help="A descriptive name for this workspace.",
            )
            description = st.text_area(
                "Description (optional)",
                placeholder="What are you trying to predict or discover?",
                help="Optional context for this project.",
                height=80,
            )
            submitted = st.form_submit_button("Create & Select", type="primary", width='stretch')

            if submitted:
                if not name.strip():
                    st.error("Project name is required.")
                else:
                    try:
                        new_project = service.create_project(
                            name=name.strip(),
                            description=description.strip(),
                        )
                        NavigationContext.set_active_project(new_project)
                        st.success(f"**{new_project.name}** is now active.")
                        st.rerun()
                    except ServiceError as err:
                        render_service_error(err)
                    except Exception as exc:
                        st.error(f"Failed to create project: {exc}")

    with col2:
        st.subheader("Your Workspaces")
        st.caption("Persisted locally in SQLite & local storage")

        projects = service.list_projects()
        if not projects:
            st.info("No projects yet. Create one to start building.")
        else:
            for p in projects:
                is_active = active_project and active_project.id == p.id
                with st.container(border=True):
                    header_cols = st.columns([3, 1])
                    with header_cols[0]:
                        badge_html = f' {pill_html("Active", "success")}' if is_active else ""
                        st.markdown(f"**{escape(p.name)}**{badge_html}", unsafe_allow_html=True)
                        if p.description:
                            st.caption(p.description)
                        st.caption(f"Created {p.created_at[:10]}")
                    with header_cols[1]:
                        if not is_active:
                            if st.button("Activate", key=f"sel_proj_{p.id}", width='stretch'):
                                NavigationContext.set_active_project(p)
                                st.rerun()

    st.divider()

    st.subheader("Workspace Activity")
    st.caption("Persisted datasets and experiments in the active project.")
    if not active_project:
        return

    dataset_service = DatasetService()
    experiment_service = ExperimentService()
    datasets = dataset_service.list_datasets(active_project.id)
    experiments = sorted(
        experiment_service.list_experiments(active_project.id),
        key=lambda item: item.started_at,
        reverse=True,
    )

    if not datasets:
        st.info("Start by opening **Datasets** and loading a demo or importing a CSV file.")
        with st.container(border=True):
            st.markdown("#### Quick-Start: Inject a Demo Dataset")
            st.caption("Jump straight into experimentation without preparing your own CSV.")
            demo_cols = st.columns(3)
            for column, (kind, label) in zip(demo_cols, QUICK_START_DEMOS):
                with column:
                    if st.button(label, key=f"demo_{kind.value}", width='stretch'):
                        _load_demo(kind, active_project.id)
        return

    if not experiments:
        st.info("Your data is ready. Open **Explore** to choose a target and prepare a modeling split.")
        return

    _render_activity_horizon(experiments[:6])


def _render_lab_bento(active_project) -> None:
    """Render the hero lab card plus dataset health and latest run cards."""
    dataset_service = DatasetService()
    experiment_service = ExperimentService()
    datasets = dataset_service.list_datasets(active_project.id)
    experiments = sorted(
        experiment_service.list_experiments(active_project.id),
        key=lambda item: item.started_at,
        reverse=True,
    )
    completed = [experiment for experiment in experiments if experiment.status == "completed"]

    hero_title = active_project.name
    hero_kicker = pill_html("Active Lab", "primary")
    if active_project.description:
        hero_body = escape(active_project.description)
    else:
        hero_body = "Isolated local artifacts for reproducible supervised and unsupervised work."
    hero_stats = render_hero_stats(
        [
            (escape(str(len(datasets))), "Datasets"),
            (escape(str(len(experiments))), "Experiments"),
            (escape(str(len(completed))), "Completed runs"),
        ]
    )
    hero_footer = f'ID: {escape(active_project.id[:8])} • created {escape(active_project.created_at[:10])}'

    active_dataset_id = st.session_state.get("active_dataset_id")
    active_dataset = (
        dataset_service.get_dataset(active_dataset_id) if active_dataset_id else None
    )
    if active_dataset is not None:
        profile = active_dataset.get_profile()
        warning_count = len(profile.quality_warnings)
        if warning_count:
            health_pill = pill_html(f"{warning_count} quality warnings", "amber")
        else:
            health_pill = pill_html("Clean profile", "success")
        health_body = (
            f"<p><strong>{escape(active_dataset.display_name)}</strong></p>"
            f"<p style='margin-top:0.35rem;'>{health_pill}</p>"
            f"<p style='margin-top:0.55rem; font-size:0.85rem; color:var(--dm-text-muted);'>"
            f"{profile.row_count:,} rows × {profile.column_count} columns • "
            f"{profile.duplicate_row_count:,} duplicate rows</p>"
        )
    else:
        health_body = (
            f"<p>{pill_html('No dataset selected', 'muted')}</p>"
            "<p style='margin-top:0.55rem; font-size:0.85rem; color:var(--dm-text-muted);'>"
            "Load a CSV or a demo in Datasets to make it the active context.</p>"
        )

    latest = experiments[0] if experiments else None
    if latest is not None:
        status_variant = "success" if latest.status == "completed" else "rose"
        latest_body = (
            f"<p><strong>{escape(latest.name)}</strong></p>"
            f"<p style='margin-top:0.35rem;'>{pill_html(latest.status.title(), status_variant)} "
            f"{pill_html(latest.task.value.title(), 'cyan')}</p>"
            f"<p style='margin-top:0.55rem; font-size:0.85rem; color:var(--dm-text-muted);'>"
            f"Primary metric: {escape(latest.primary_metric)} • started {_relative_time(latest.started_at)}</p>"
        )
    else:
        latest_body = (
            f"<p>{pill_html('No experiments yet', 'muted')}</p>"
            "<p style='margin-top:0.55rem; font-size:0.85rem; color:var(--dm-text-muted);'>"
            "Prepare a split in Explore, then train in Experiment.</p>"
        )

    render_bento_grid(
        [
            {
                "title": hero_title,
                "kicker_html": hero_kicker,
                "body_html": f"<p>{hero_body}</p>{hero_stats}",
                "footer_html": hero_footer,
                "span": "2x1",
                "hero": True,
            },
            {
                "title": "Active Dataset Health",
                "body_html": health_body,
            },
            {
                "title": "Latest Experiment",
                "body_html": latest_body,
            },
        ]
    )


def _render_activity_horizon(experiments) -> None:
    """Render the experiment activity timeline with status pills and relative times."""
    entries = []
    for experiment in experiments:
        status_variant = "success" if experiment.status == "completed" else "rose"
        detail = (
            f"{experiment.task.value.title()} • primary metric: {experiment.primary_metric}"
            f" • seed {experiment.random_seed}"
        )
        entries.append(
            {
                "title": experiment.name,
                "when": _relative_time(experiment.started_at),
                "detail": detail,
                "pill_label": experiment.status.title(),
                "pill_variant": status_variant,
            }
        )
    render_activity_timeline(entries)
    st.caption("Open Compare, Predict, or Explain & Export to continue with saved results.")
