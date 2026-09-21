"""Application navigation and global session context."""

from __future__ import annotations

from typing import Callable, Dict, Optional

import streamlit as st

from datamind.contracts import ProjectSummary
from datamind.services.projects import ProjectService


class NavigationContext:
    """Manages session state for the active project and current page."""

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
        """Set the currently active project in session state."""
        st.session_state["active_project"] = project
        st.session_state["active_project_id"] = project.id if project else None


PAGES: Dict[str, str] = {
    "Home": "Overview and project management",
    "Datasets": "Dataset upload, demos, and profiling (M1)",
    "Explore": "Development data EDA and split setup (M2a)",
    "Experiment": "Algorithm selection, training, and CV (M2b)",
    "Compare": "Consistent run comparison and leaderboard (M3b)",
    "Predict": "Single and batch prediction (M3b)",
    "Explain & Export": "Model diagnostics and experiment report export (M4)",
    "Clustering": "K-Means discovery and clustering lab (M5a)",
    "Discover": "Algorithm intuition cards and toy playground (M5b)",
}


def render_sidebar(pages: Dict[str, Callable[[], None]]) -> str:
    """Render the sidebar brand, project switcher, and explicit page navigation."""
    with st.sidebar:
        st.markdown("### 🧠 DataMind")
        st.caption("Interactive ML Discovery Platform • v0.1.0 (M0)")
        st.divider()

        # Project switcher in sidebar
        service = ProjectService()
        projects = service.list_projects()

        current_project = NavigationContext.get_active_project()

        st.markdown("**Workspace Project**")
        if projects:
            options = {p.id: p.name for p in projects}
            selected_idx = 0
            if current_project and current_project.id in options:
                selected_idx = list(options.keys()).index(current_project.id)

            selected_id = st.selectbox(
                "Active Project",
                options=list(options.keys()),
                index=selected_idx,
                format_func=lambda pid: options[pid],
                label_visibility="collapsed",
                key="sidebar_project_select",
            )
            if selected_id != (current_project.id if current_project else None):
                NavigationContext.set_active_project(service.get_project(selected_id))
                st.rerun()
        else:
            st.caption("No projects created yet.")
            st.info("Create a project on the Home page.")

        st.divider()

        # Explicit page selector
        st.markdown("**Navigation**")
        page_names = list(pages.keys())
        current_selection = st.session_state.get("selected_page", "Home")
        current_idx = page_names.index(current_selection) if current_selection in page_names else 0

        selected_page = st.radio(
            "Go to",
            page_names,
            index=current_idx,
            label_visibility="collapsed",
            key="nav_radio",
        )
        st.session_state["selected_page"] = selected_page

        st.divider()
        st.caption("💻 Local CPU Runtime • Loopback 127.0.0.1")

    return selected_page
