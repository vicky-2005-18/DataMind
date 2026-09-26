"""Application navigation and global session context."""

from __future__ import annotations

from typing import Callable, Dict, Optional

import streamlit as st

from datamind.contracts import ProjectSummary
from datamind.services.datasets import DatasetService
from datamind.services.projects import ProjectService

DATASET_DRAFT_KEYS = {
    "explore_task_choice",
    "explore_target_choice",
    "explore_numeric_features",
    "explore_categorical_features",
    "explore_test_frac",
    "explore_cv_folds",
    "explore_random_seed",
    "eda_feat_select",
    "exp_task",
    "exp_target",
    "exp_cv_folds",
    "exp_algo_multiselect",
    "exp_name_input",
    "latest_experiment",
}

PROJECT_SELECT_KEY = "sidebar_project_select"
# Selectbox widget state survives reruns, so programmatic changes must be pushed into it before instantiation or the sidebar sync reverts them.
_PROJECT_SELECT_PENDING = "_project_select_pending"


class NavigationContext:
    """Manages session state for the active project and current page."""

    @staticmethod
    def invalidate_dataset_draft() -> None:
        for key in list(st.session_state):
            if key in DATASET_DRAFT_KEYS or key.startswith(("view_", "split_")):
                st.session_state.pop(key, None)

    @staticmethod
    def set_active_dataset(dataset_id: Optional[str]) -> bool:
        """Set the active dataset and invalidate dependent transient state on change."""
        if st.session_state.get("active_dataset_id") == dataset_id:
            return False
        NavigationContext.invalidate_dataset_draft()
        st.session_state["active_dataset_id"] = dataset_id
        return True

    @staticmethod
    def initialize() -> None:
        """Initialize session state keys if not already set."""
        if "active_project_id" not in st.session_state:
            st.session_state["active_project_id"] = None
        if "active_project" not in st.session_state:
            st.session_state["active_project"] = None
        if "selected_page" not in st.session_state:
            st.session_state["selected_page"] = "Home"

    @staticmethod
    def get_active_project() -> Optional[ProjectSummary]:
        """Get the currently selected ProjectSummary, refreshing from DB if needed."""
        project_id = st.session_state.get("active_project_id")
        if not project_id:
            st.session_state["active_project"] = None
            return None

        # Verify project still exists in DB
        service = ProjectService()
        project = service.get_project(project_id)
        st.session_state["active_project"] = project
        if not project:
            st.session_state["active_project_id"] = None
        return project

    @staticmethod
    def set_active_project(project: Optional[ProjectSummary]) -> None:
        """Set the project and clear dataset-dependent transient state on change."""
        new_id = project.id if project else None
        if st.session_state.get("active_project_id") != new_id:
            NavigationContext.invalidate_dataset_draft()
            st.session_state["active_dataset_id"] = None
        st.session_state["active_project"] = project
        st.session_state["active_project_id"] = new_id
        st.session_state[_PROJECT_SELECT_PENDING] = new_id


PAGES: Dict[str, str] = {
    "Home": "Manage your workspace and projects",
    "Datasets": "Import, validate, and profile data",
    "Explore": "Understand data and prepare a split",
    "Experiment": "Configure and train supervised models",
    "Compare": "Compare compatible experiment results",
    "Predict": "Run single or batch predictions",
    "Explain & Export": "Inspect models and export evidence",
    "Clustering": "Discover structure with K-Means",
    "Discover": "Learn algorithms through playgrounds",
}

NAV_GROUPS = {
    "Workspace": ("Home",),
    "Prepare": ("Datasets", "Explore"),
    "Model": ("Experiment", "Compare"),
    "Deliver": ("Predict", "Explain & Export"),
    "Learn": ("Clustering", "Discover"),
}

PAGE_GROUP = {
    page: group
    for group, group_pages in NAV_GROUPS.items()
    for page in group_pages
}


def render_sidebar(pages: Dict[str, Callable[[], None]]) -> str:
    """Render the sidebar brand, project switcher, and explicit page navigation."""
    with st.sidebar:
        st.markdown(
            """
            <div class="dm-brand">
                <span class="dm-brand-mark">DM</span><span class="dm-brand-name">DataMind</span>
                <p class="dm-brand-copy">Interactive machine learning workspace</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()

        service = ProjectService()
        projects = service.list_projects()

        current_project = NavigationContext.get_active_project()

        st.markdown('<p class="dm-stage">Current workspace</p>', unsafe_allow_html=True)
        if projects:
            options = {p.id: p.name for p in projects}
            pending = st.session_state.pop(_PROJECT_SELECT_PENDING, None)
            if pending is not None and pending in options:
                st.session_state[PROJECT_SELECT_KEY] = pending
            selected_idx = 0
            if current_project and current_project.id in options:
                selected_idx = list(options.keys()).index(current_project.id)

            selected_id = st.selectbox(
                "Active Project",
                options=list(options.keys()),
                index=selected_idx,
                format_func=lambda pid: options[pid],
                label_visibility="collapsed",
                key=PROJECT_SELECT_KEY,
            )
            if selected_id != (current_project.id if current_project else None):
                NavigationContext.set_active_project(service.get_project(selected_id))
                st.rerun()

            dataset_service = DatasetService()
            active_dataset_id = st.session_state.get("active_dataset_id")
            if current_project and active_dataset_id:
                dataset = dataset_service.get_dataset(active_dataset_id)
                if dataset:
                    st.markdown(
                        f"""
                        <div class="dm-context">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <p class="dm-context-label">Active dataset</p>
                                <span class="dm-pill dm-pill-cyan" style="font-size: 0.68rem; padding: 0.15rem 0.45rem;">
                                    {dataset.row_count:,}r · {dataset.column_count}c
                                </span>
                            </div>
                            <p class="dm-context-value">{dataset.display_name}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("No projects created yet.")
            st.info("Create a project on the Home page.")

        st.divider()

        current_selection = st.session_state.get("selected_page", "Home")
        current_group = PAGE_GROUP.get(current_selection, "Workspace")

        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                <span class="dm-stage" style="margin: 0;">Workflow Stage</span>
                <span class="dm-pill dm-pill-primary">{current_group}</span>
            </div>
            <p class="dm-nav-groups" style="font-size: 0.72rem; color: var(--dm-muted); margin-bottom: 0.5rem;">
                Workspace → Prepare → Model → Deliver → Learn
            </p>
            """,
            unsafe_allow_html=True,
        )

        page_names = list(pages.keys())
        current_selection = st.session_state.get("selected_page", "Home")
        current_idx = page_names.index(current_selection) if current_selection in page_names else 0

        selected_page = st.radio(
            "Navigate",
            page_names,
            index=current_idx,
            key="nav_radio",
        )
        st.session_state["selected_page"] = selected_page

        st.divider()
        st.markdown(
            """
            <div class="dm-runtime">
                <span class="dm-runtime-dot" aria-hidden="true"></span>
                Local runtime · 127.0.0.1
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page
