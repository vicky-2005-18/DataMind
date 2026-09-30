"""Reusable Streamlit UI components for DataMind.

This package re-exports all components from the original components.py
to maintain backward compatibility with existing imports.
"""

# Re-export everything from the original components.py
from datamind.ui.components.badges import (
    pill_html,
    render_pill,
    render_rank_medal,
)
from datamind.ui.components.cards import (
    render_bento_card,
    render_bento_grid,
    render_hero_stats,
)
from datamind.ui.components.charts import style_plotly_figure
from datamind.ui.components.forms import (
    render_error_state,
    render_loading_state,
    render_service_error,
)
from datamind.ui.components.layout import (
    render_active_project_banner,
    render_empty_state,
    render_header,
    render_workflow_stepper,
)
from datamind.ui.components.styles import (
    GLOBAL_STYLES,
    PILL_CLASSES,
    BentoSpan,
    PillVariant,
    apply_global_styles,
)
from datamind.ui.components.tables import (
    render_activity_timeline,
    render_fold_ticker,
    render_probability_bars,
    render_split_bar,
)

__all__ = [
    # Styles
    "apply_global_styles",
    "GLOBAL_STYLES",
    "PILL_CLASSES",
    "PillVariant",
    "BentoSpan",
    # Badges
    "pill_html",
    "render_pill",
    "render_rank_medal",
    # Cards
    "render_bento_card",
    "render_bento_grid",
    "render_hero_stats",
    # Layout
    "render_active_project_banner",
    "render_empty_state",
    "render_header",
    "render_workflow_stepper",
    # Forms
    "render_service_error",
    "render_loading_state",
    "render_error_state",
    # Tables
    "render_split_bar",
    "render_activity_timeline",
    "render_fold_ticker",
    "render_probability_bars",
    # Charts
    "style_plotly_figure",
]
