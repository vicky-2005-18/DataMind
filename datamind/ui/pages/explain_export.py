"""Explain & Export page placeholder for M4."""

from __future__ import annotations

from datamind.ui.components import (
    render_active_project_banner,
    render_empty_state,
    render_header,
)
from datamind.ui.navigation import NavigationContext


def render_explain_export_page() -> None:
    """Render the Explain & Export page."""
    render_header(
        title="Model Explanations & Export",
        subtitle="Inspect non-causal permutation importance diagnostics and export reproducible bundles",
    )
    active_project = NavigationContext.get_active_project()
    render_active_project_banner(active_project)

    render_empty_state(
        milestone="M4 — Explain & Export",
        page_name="Explanations & Artifact Export",
        description=(
            "Calculate bounded development-set permutation importances clearly labeled as non-causal diagnostics. "
            "Export complete ZIP bundles containing fitted pipelines, manifests, environment records, "
            "and human-readable HTML/Markdown experiment reports."
        ),
        next_action="Export capabilities become available in M4.",
    )
