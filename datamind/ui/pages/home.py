"""Home page: workspace overview, project creation, and project selection."""

from __future__ import annotations

import streamlit as st

from datamind.contracts import ServiceError
from datamind.services.projects import ProjectService
from datamind.ui.components import render_active_project_banner, render_header, render_service_error
from datamind.ui.navigation import NavigationContext


def render_home_page() -> None:
    """Render the Home page for DataMind."""
    render_header(
        title="Welcome to DataMind",
        subtitle="An Interactive Machine Learning Discovery & Experimentation Platform",
    )

    service = ProjectService()
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    st.write("")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("Create a New Project")
        st.caption("Organize your datasets, modeling splits, and ML experiments.")

        with st.form("create_project_form", clear_on_submit=True):
            name = st.text_input(
                "Project Name",
                placeholder="e.g. Iris Classification Lab",
                help="Enter a unique name for your project.",
            )
            description = st.text_area(
                "Description (optional)",
                placeholder="Brief notes about the goals of this experiment workspace...",
                help="Optional context or notes.",
            )
            submitted = st.form_submit_button("Create Project", type="primary")

            if submitted:
                if not name.strip():
                    st.error("Project name cannot be empty.")
                else:
                    try:
                        new_project = service.create_project(
                            name=name.strip(),
                            description=description.strip(),
                        )
                        NavigationContext.set_active_project(new_project)
                        st.success(f"Project **{new_project.name}** created and selected!")
                        st.rerun()
                    except ServiceError as err:
                        render_service_error(err)
                    except Exception as exc:
                        st.error(f"Failed to create project: {exc}")

    with col2:
        st.subheader("Your Projects")
        st.caption("Projects persisted in local SQLite storage.")

        projects = service.list_projects()
        if not projects:
            st.info("No projects found. Create your first project using the form on the left.")
        else:
            for p in projects:
                is_active = active_project and active_project.id == p.id
                with st.container(border=True):
                    header_cols = st.columns([3, 1])
                    with header_cols[0]:
                        st.markdown(f"**{p.name}** {'🔹 *(Active)*' if is_active else ''}")
                        if p.description:
                            st.caption(p.description)
                        st.caption(f"Created: `{p.created_at[:19].replace('T', ' ')} UTC` • ID: `{p.id[:8]}`")
                    with header_cols[1]:
                        if not is_active:
                            if st.button("Select", key=f"sel_proj_{p.id}"):
                                NavigationContext.set_active_project(p)
                                st.rerun()

    st.divider()

    st.subheader("Recent Activity")
    st.caption("Experiments and model evaluations across this workspace.")
    st.info(
        "ℹ️ **No experiments run yet.** DataMind never fabricates activity. "
        "Once you load a dataset (M1) and train models (M2), verifiable results will appear here."
    )
