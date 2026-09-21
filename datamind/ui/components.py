"""Reusable Streamlit UI components and layout helpers for DataMind."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from datamind.contracts import ProjectSummary, ServiceError


def render_header(title: str, subtitle: str) -> None:
    """Render consistent page title and subtitle."""
    st.title(title)
    st.markdown(f"*{subtitle}*")
    st.divider()


def render_active_project_banner(project: Optional[ProjectSummary]) -> None:
    """Render a notification banner indicating current project context."""
    if project:
        st.info(f"📁 **Active Project:** {project.name} `[{project.id[:8]}]`")
    else:
        st.warning("⚠️ **No Active Project Selected.** Please select or create a project on the **Home** page to begin.")


def render_empty_state(
    milestone: str,
    page_name: str,
    description: str,
    next_action: Optional[str] = None,
) -> None:
    """Render an honest empty state for future milestone pages without fake controls."""
    st.subheader(f"🚧 {page_name}")
    st.markdown(
        f"""
        > **Status: Scheduled for {milestone}**

        {description}
        """
    )
    if next_action:
        st.info(f"💡 **Next step:** {next_action}")
    else:
        st.caption("No mock controls or fabricated data are shown here until this milestone is implemented.")


def render_service_error(error: Exception) -> None:
    """Render a standardized error callout with actionable guidance."""
    if isinstance(error, ServiceError):
        st.error(f"**[{error.code.value}]** {error.user_message}")
        if error.field:
            st.caption(f"Affects field: `{error.field}`")
    else:
        st.error(f"**An unexpected error occurred:** {error}")
