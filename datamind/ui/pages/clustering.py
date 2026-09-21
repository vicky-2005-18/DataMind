"""Clustering page placeholder for M5a."""

from __future__ import annotations

from datamind.ui.components import (
    render_active_project_banner,
    render_empty_state,
    render_header,
)
from datamind.ui.navigation import NavigationContext


def render_clustering_page() -> None:
    """Render the Clustering page."""
    render_header(
        title="Unsupervised Clustering Lab",
        subtitle="K-Means clustering, elbow analysis, silhouette validation, and 2D projections",
    )
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    render_empty_state(
        milestone="M5a — Clustering",
        page_name="K-Means Lab",
        description=(
            "Unsupervised clustering on numeric features without targets or accuracy claims. "
            "Includes elbow inertia sweeps, mathematically guarded silhouette scores, "
            "and 2D PCA display projections distinct from the underlying feature space."
        ),
        next_action="Clustering features arrive in M5a.",
    )
