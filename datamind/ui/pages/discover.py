"""Discover page placeholder for M5b."""

from __future__ import annotations

from datamind.ui.components import (
    render_active_project_banner,
    render_empty_state,
    render_header,
)
from datamind.ui.navigation import NavigationContext


def render_discover_page() -> None:
    """Render the Discover page."""
    render_header(
        title="Algorithm Discovery & Educational Playground",
        subtitle="Explore algorithm cards and experiment with 2D decision boundary playgrounds",
    )
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    render_empty_state(
        milestone="M5b — Discovery",
        page_name="Algorithm Cards & Interactive Playground",
        description=(
            "Curated algorithm reference cards covering intuition, assumptions, and hyperparameter impacts. "
            "Includes interactive 2D playgrounds for decision trees, kNN decision boundaries, and clustering "
            "with immediate visual feedback on synthetic datasets."
        ),
        next_action="Educational discovery features arrive in M5b.",
    )
