"""DataMind Design System - Phase A Foundation.

Centralized color, spacing, and typography tokens to ensure consistency
across all pages and components.
"""

from __future__ import annotations


class ColorTokens:
    """Color tokens for the DataMind dark theme interface."""

    # Background colors
    BACKGROUND_BASE = "#0E1117"
    BACKGROUND_SURFACE = "#161B22"
    BACKGROUND_ELEVATED = "#1F2630"

    # Border/divider
    BORDER = "#2A3140"

    # Text colors
    TEXT_PRIMARY = "#E6E8EB"
    TEXT_SECONDARY = "#9AA4B2"
    TEXT_DISABLED = "#5B6472"

    # Accent colors
    ACCENT_PRIMARY = "#6C63FF"  # Male/series A, primary actions
    ACCENT_SECONDARY = "#12B8C4"  # Female/series B, links

    # Status colors
    STATUS_SUCCESS = "#2ECC71"
    STATUS_WARNING = "#F5A623"
    STATUS_ERROR = "#EF4444"


class SpacingTokens:
    """Spacing tokens based on 8px base unit."""

    BASE_UNIT = 8

    # Card padding
    CARD_PADDING_COMPACT = 16
    CARD_PADDING_COMFORTABLE = 24

    # Section gaps
    SECTION_GAP = 32

    # Chart-specific spacing
    CHART_TITLE_TO_PLOT_MIN = 16
    CHART_TITLE_MARGIN_TOP = 60
    CHART_MARGIN_LEFT = 60
    CHART_MARGIN_RIGHT = 30
    CHART_MARGIN_BOTTOM = 50


class TypographyTokens:
    """Typography tokens for consistent text hierarchy."""

    # Font family (Inter/system-ui stack)
    FONT_FAMILY = "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

    # Font sizes
    PAGE_TITLE_SIZE = 24
    PAGE_TITLE_WEIGHT = 600  # semibold

    SECTION_HEADER_SIZE = 16
    SECTION_HEADER_WEIGHT = 600  # semibold

    BODY_SIZE = 14
    BODY_WEIGHT = 400  # regular

    CHART_TITLE_SIZE = 14
    CHART_TITLE_WEIGHT = 500  # medium

    AXIS_LEGEND_SIZE = 12
    AXIS_LEGEND_WEIGHT = 400  # regular


class Theme:
    """Main theme class aggregating all design tokens."""

    color = ColorTokens()
    spacing = SpacingTokens()
    typography = TypographyTokens()

    @staticmethod
    def get_css_variables() -> str:
        """Generate CSS custom properties for use in Streamlit markdown."""
        return f"""
        <style>
        :root {{
            --dm-bg-base: {Theme.color.BACKGROUND_BASE};
            --dm-bg-surface: {Theme.color.BACKGROUND_SURFACE};
            --dm-bg-elevated: {Theme.color.BACKGROUND_ELEVATED};
            --dm-border: {Theme.color.BORDER};
            --dm-text-primary: {Theme.color.TEXT_PRIMARY};
            --dm-text-secondary: {Theme.color.TEXT_SECONDARY};
            --dm-text-disabled: {Theme.color.TEXT_DISABLED};
            --dm-accent-primary: {Theme.color.ACCENT_PRIMARY};
            --dm-accent-secondary: {Theme.color.ACCENT_SECONDARY};
            --dm-status-success: {Theme.color.STATUS_SUCCESS};
            --dm-status-warning: {Theme.color.STATUS_WARNING};
            --dm-status-error: {Theme.color.STATUS_ERROR};
            --dm-font-family: {Theme.typography.FONT_FAMILY};
            --dm-spacing-base: {Theme.spacing.BASE_UNIT}px;
        }}
        </style>
        """
