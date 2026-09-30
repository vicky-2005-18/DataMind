"""Layout and header components."""

from html import escape
from typing import Optional

from datamind.contracts import ProjectSummary
from datamind.ui.components.badges import pill_html

import streamlit as st


def render_header(title: str, subtitle: str) -> None:
    """Render consistent page title, eyebrow, and luminous divider."""
    st.markdown('<p class="dm-eyebrow">DataMind AI Laboratory</p>', unsafe_allow_html=True)
    st.title(title, anchor=False)
    st.markdown(f'<p class="dm-page-subtitle">{escape(subtitle)}</p>', unsafe_allow_html=True)
    st.markdown('<div class="dm-rule" aria-hidden="true"></div>', unsafe_allow_html=True)


def render_workflow_stepper(current_stage: str = "Workspace") -> None:
    """Render an aesthetic 5-stage workflow rail with active stage highlight."""
    stages = [
        ("1", "Workspace", "Home", "Select or initialize your project environment"),
        ("2", "Prepare", "Data", "Profile schemas, check hygiene & create splits"),
        ("3", "Model", "Train", "Run cross-validation & benchmark candidates"),
        ("4", "Deliver", "Inference", "Simulate predictions & export audit bundles"),
        ("5", "Learn", "Studio", "Explore K-Means clusters & algorithm sandboxes"),
    ]
    cols = st.columns(len(stages))
    for col, (num, name, tag, desc) in zip(cols, stages):
        is_active = name.lower() == current_stage.lower()
        active_class = " active" if is_active else ""
        pill = pill_html(tag, "primary" if is_active else "cyan")
        with col:
            st.markdown(
                f"""
                <div class="dm-workflow-card{active_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="dm-workflow-step-num">STAGE 0{escape(num)}</span>
                        {pill}
                    </div>
                    <div class="dm-workflow-step-name">{escape(name)}</div>
                    <div class="dm-workflow-step-desc">{escape(desc)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_active_project_banner(project: Optional[ProjectSummary]) -> None:
    """Render an informative status pill indicating current workspace context."""
    if project:
        desc_str = f" — {escape(project.description)}" if project.description else ""
        active_pill = pill_html("Active", "primary")
        st.markdown(
            f"""
            <div class="dm-project-banner">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    {active_pill}
                    <div>
                        <span style="font-weight: 750; font-size: 1rem; color: var(--dm-text-strong);">{escape(project.name)}</span>
                        <span style="color: var(--dm-text-muted); font-size: 0.85rem;">{desc_str}</span>
                    </div>
                </div>
                <div class="dm-project-id">ID: {escape(project.id[:8])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            "**No Active Project Selected.** Please select or create a project on the **Home** page to begin."
        )


def render_empty_state(
    milestone: str,
    page_name: str,
    description: str,
    next_action: Optional[str] = None,
) -> None:
    """Render an honest empty state for future milestone pages without fake controls."""
    st.subheader(page_name)
    st.markdown(
        f"""
        > **Status: Scheduled for {escape(milestone)}**

        {escape(description)}
        """
    )
    if next_action:
        st.info(f"**Next step:** {next_action}")
    else:
        st.caption(
            "No mock controls or fabricated data are shown here until this milestone is implemented."
        )
