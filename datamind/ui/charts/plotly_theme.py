"""Shared Plotly theme for DataMind charts.

This provides a consistent styling and tooltip behavior across all charts,
preventing positioning bugs and ensuring professional appearance.
"""

from __future__ import annotations

import plotly.graph_objects as go

from datamind.ui.theme import Theme


def get_plotly_theme() -> go.layout.Template:
    """Return the shared Plotly template for all DataMind charts.

    This template ensures:
    - Consistent colors and fonts across all charts
    - Proper tooltip positioning (no overlap with titles/toolbar)
    - Fixed margins to prevent layout collisions
    - Professional dark theme appearance

    All chart-producing functions must import and apply this template.
    """
    template = go.layout.Template()

    # Layout settings
    template.layout = go.Layout(
        # Margins - critical for preventing tooltip/title overlap
        margin=dict(
            t=Theme.spacing.CHART_TITLE_MARGIN_TOP,  # Top margin for title
            l=Theme.spacing.CHART_MARGIN_LEFT,       # Left margin for axis labels
            r=Theme.spacing.CHART_MARGIN_RIGHT,      # Right margin
            b=Theme.spacing.CHART_MARGIN_BOTTOM,     # Bottom margin for x-axis
        ),
        # Font settings
        font=dict(
            family=Theme.typography.FONT_FAMILY,
            size=Theme.typography.BODY_SIZE,
            color=Theme.color.TEXT_PRIMARY,
        ),
        title_font=dict(
            family=Theme.typography.FONT_FAMILY,
            size=Theme.typography.CHART_TITLE_SIZE,
            color=Theme.color.TEXT_PRIMARY,
        ),
        # Background colors
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        # Hover behavior - this is the key fix for tooltip positioning
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=Theme.color.BACKGROUND_ELEVATED,
            bordercolor=Theme.color.BORDER,
            font=dict(
                family=Theme.typography.FONT_FAMILY,
                size=12,
                color=Theme.color.TEXT_PRIMARY,
            ),
            # namelength=-1 shows full trace names (important for categorical data)
            namelength=-1,
            align="left",
        ),
        # Axis styling
        xaxis=dict(
            showgrid=True,
            gridcolor=Theme.color.BORDER,
            linecolor=Theme.color.BORDER,
            tickfont=dict(
                family=Theme.typography.FONT_FAMILY,
                size=Theme.typography.AXIS_LEGEND_SIZE,
                color=Theme.color.TEXT_SECONDARY,
            ),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=Theme.color.BORDER,
            linecolor=Theme.color.BORDER,
            tickfont=dict(
                family=Theme.typography.FONT_FAMILY,
                size=Theme.typography.AXIS_LEGEND_SIZE,
                color=Theme.color.TEXT_SECONDARY,
            ),
        ),
        # Legend styling
        legend=dict(
            font=dict(
                family=Theme.typography.FONT_FAMILY,
                size=Theme.typography.AXIS_LEGEND_SIZE,
                color=Theme.color.TEXT_SECONDARY,
            ),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=Theme.color.BORDER,
        ),
    )

    return template


def apply_shared_theme(fig: go.Figure, title: str | None = None) -> go.Figure:
    """Apply the shared theme to a Plotly figure.

    Args:
        fig: The Plotly figure to theme
        title: Optional title to set on the figure

    Returns:
        The themed figure ready for rendering

    Usage:
        fig = px.bar(data, x="category", y="value")
        fig = apply_shared_theme(fig, "My Chart Title")
        st.plotly_chart(fig, width='stretch')
    """
    # Apply the template
    fig.update_layout(template=get_plotly_theme())

    # Set title if provided
    if title:
        fig.update_layout(title=title)

    # Apply consistent hover templates for common chart types
    # This ensures tooltip content is consistent across all charts
    # Note: We don't override hover templates here to preserve Plotly's automatic
    # group/legend handling which is critical for categorical data
    # Individual charts can set custom hover templates if needed

    return fig
