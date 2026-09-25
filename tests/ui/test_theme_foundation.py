"""Phase 1 foundation: design tokens and reusable UI primitives."""

from __future__ import annotations

from datamind.ui.components import GLOBAL_STYLES, PILL_CLASSES, pill_html

REQUIRED_TOKENS = (
    "--dm-canvas",
    "--dm-surface-primary",
    "--dm-surface-elevated",
    "--dm-surface-glass",
    "--dm-primary",
    "--dm-primary-glow",
    "--dm-accent-cyan",
    "--dm-accent-emerald",
    "--dm-accent-amber",
    "--dm-accent-rose",
    "--dm-border-subtle",
    "--dm-border-focus",
    "--dm-text-strong",
    "--dm-text-muted",
    "--dm-text-dim",
    "--dm-radius-sm",
    "--dm-radius-md",
    "--dm-radius-lg",
    "--dm-shadow-bento",
    "--dm-shadow-glow",
)


def test_global_styles_include_design_tokens() -> None:
    for token in REQUIRED_TOKENS:
        assert token in GLOBAL_STYLES


def test_global_styles_respect_reduced_motion_and_focus() -> None:
    assert "prefers-reduced-motion" in GLOBAL_STYLES
    assert "outline: 3px solid rgba(99, 102, 241, 0.4)" in GLOBAL_STYLES
    assert "cursor: pointer" in GLOBAL_STYLES
    assert "dm-bento-card" in GLOBAL_STYLES
    assert 'html[data-theme="light"]' in GLOBAL_STYLES


def test_pill_html_escapes_and_labels_variant() -> None:
    html = pill_html("<script>", "success")
    assert "&lt;script&gt;" in html
    assert "dm-pill-success" in html
    assert PILL_CLASSES["amber"].endswith("dm-pill-amber")
