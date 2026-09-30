"""Chart styling components."""

from typing import Optional

from datamind.ui.charts.plotly_theme import apply_shared_theme


def style_plotly_figure(fig, title: Optional[str] = None):
    """Apply the shared DataMind theme to Plotly figures.

    This function now uses the centralized theme system to ensure consistent
    styling and proper tooltip positioning across all charts.

    Args:
        fig: The Plotly figure to style
        title: Optional title to set on the figure

    Returns:
        The themed figure ready for rendering
    """
    return apply_shared_theme(fig, title)
