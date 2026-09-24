"""Reusable Streamlit UI components and layout helpers for DataMind."""

from __future__ import annotations

from typing import Optional

import streamlit as st

from datamind.contracts import ProjectSummary, ServiceError

GLOBAL_STYLES = """
<style>
:root {
    --dm-primary: #4f46e5;
    --dm-primary-hover: #4338ca;
    --dm-accent: #0f766e;
    --dm-canvas: #f6f7fb;
    --dm-surface: #ffffff;
    --dm-text: #172033;
    --dm-muted: #5f6b7a;
    --dm-border: #dde2ea;
    --dm-success: #15803d;
    --dm-warning: #b45309;
    --dm-error: #b91c1c;
    --dm-radius-sm: .65rem;
    --dm-radius-md: .85rem;
    --dm-shadow-sm: 0 1px 2px rgba(15, 23, 42, .05);
}
.stApp { background: var(--dm-canvas); color: var(--dm-text); }
[data-testid="stMainBlockContainer"] { padding-top: 2.25rem; padding-bottom: 4rem; max-width: 1440px; }
[data-testid="stSidebar"] { border-right: 1px solid var(--dm-border); }
[data-testid="stSidebarContent"] { padding: .75rem; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .75rem; }
[data-testid="stSidebar"] .stRadio > label { color: var(--dm-muted); font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: .2rem; }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] { border-radius: var(--dm-radius-sm); padding: .45rem .6rem; transition: background-color .15s ease, color .15s ease; }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover { background: #eef2ff; }
[data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] { background: var(--dm-surface); border-color: var(--dm-border); border-radius: .9rem; box-shadow: var(--dm-shadow-sm); }
[data-testid="stMetric"] { background: var(--dm-surface); border: 1px solid var(--dm-border); border-radius: var(--dm-radius-md); box-shadow: var(--dm-shadow-sm); padding: 1rem; }
[data-testid="stAlert"] { border-radius: var(--dm-radius-md); }
[data-baseweb="input"] > div, [data-baseweb="select"] > div, textarea { border-radius: var(--dm-radius-sm) !important; }
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button { min-height: 2.65rem; border-radius: var(--dm-radius-sm); font-weight: 650; transition: border-color .15s ease, background-color .15s ease, box-shadow .15s ease; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] { background: var(--dm-primary); border-color: var(--dm-primary); }
.stButton > button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] > button[kind="primary"]:hover { background: var(--dm-primary-hover); border-color: var(--dm-primary-hover); }
button:focus-visible, input:focus-visible, textarea:focus-visible, [role="radio"]:focus-visible, [role="combobox"]:focus-visible { outline: 3px solid rgba(79, 70, 229, .32) !important; outline-offset: 2px; }
[data-testid="stDataFrame"], [data-testid="stTable"] { background: var(--dm-surface); border: 1px solid var(--dm-border); border-radius: .8rem; overflow: hidden; }
[data-testid="stExpander"] { background: var(--dm-surface); border-color: var(--dm-border); border-radius: var(--dm-radius-md); }
hr { border-color: var(--dm-border) !important; }
.dm-eyebrow { color: var(--dm-primary); font-size: .76rem; font-weight: 800; letter-spacing: .11em; margin: 0 0 .35rem; text-transform: uppercase; }
h1 { color: var(--dm-text); letter-spacing: -.035em !important; line-height: 1.08 !important; }
.dm-page-subtitle { color: var(--dm-muted); font-size: 1.02rem; line-height: 1.65; margin: -.25rem 0 0; max-width: 52rem; }
.dm-rule { background: linear-gradient(90deg, var(--dm-primary), var(--dm-accent), transparent); border-radius: 999px; height: 3px; margin: 1.1rem 0 1.6rem; width: 7rem; }
.dm-brand { padding: .5rem 0 .25rem; }
.dm-brand-mark { align-items: center; background: linear-gradient(135deg, var(--dm-primary), var(--dm-accent)); border-radius: .75rem; color: white; display: inline-flex; font-size: 1rem; font-weight: 800; height: 2.5rem; justify-content: center; margin-right: .65rem; width: 2.5rem; }
.dm-brand-name { color: var(--dm-text); font-size: 1.25rem; font-weight: 800; letter-spacing: -.025em; }
.dm-brand-copy { color: var(--dm-muted); font-size: .79rem; margin: .35rem 0 0; }
.dm-stage { color: var(--dm-muted); font-size: .74rem; font-weight: 750; letter-spacing: .08em; margin: .65rem 0 .15rem; text-transform: uppercase; }
.dm-context { background: #f8fafc; border: 1px solid var(--dm-border); border-radius: var(--dm-radius-md); padding: .75rem; }
.dm-context-label { color: var(--dm-muted); font-size: .7rem; font-weight: 750; letter-spacing: .08em; margin: 0; text-transform: uppercase; }
.dm-context-value { color: var(--dm-text); font-size: .88rem; font-weight: 700; margin: .15rem 0 0; overflow-wrap: anywhere; }
.dm-nav-groups { color: var(--dm-muted); font-size: .75rem; line-height: 1.6; margin: 0 0 .2rem; }
.dm-runtime { align-items: center; color: var(--dm-muted); display: flex; font-size: .78rem; gap: .45rem; }
.dm-runtime-dot { background: #16a34a; border-radius: 50%; height: .5rem; width: .5rem; }
@media (max-width: 1024px) {
    [data-testid="stMainBlockContainer"] { padding-left: 1.5rem; padding-right: 1.5rem; }
}
@media (max-width: 768px) {
    [data-testid="stMainBlockContainer"] { padding-left: 1rem; padding-right: 1rem; padding-top: 1.25rem; }
    h1 { font-size: 2rem !important; }
    .dm-page-subtitle { font-size: .95rem; }
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: min(100%, 18rem) !important; flex: 1 1 18rem !important; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { scroll-behavior: auto !important; transition-duration: .01ms !important; }
}
</style>
"""


def apply_global_styles() -> None:
    """Apply the shared DataMind visual system."""
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)


def render_header(title: str, subtitle: str) -> None:
    """Render consistent page title and subtitle."""
    st.markdown('<p class="dm-eyebrow">DataMind workspace</p>', unsafe_allow_html=True)
    st.title(title, anchor=False)
    st.markdown(f'<p class="dm-page-subtitle">{subtitle}</p>', unsafe_allow_html=True)
    st.markdown('<div class="dm-rule" aria-hidden="true"></div>', unsafe_allow_html=True)


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
