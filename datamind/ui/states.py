"""Shared state components for DataMind UI.

Provides consistent empty, loading, and error states across all pages.
"""

from __future__ import annotations

import streamlit as st
from datamind.ui.theme import Theme


def empty_state(
    title: str,
    description: str,
    icon: str = "📭",
    action_text: str | None = None,
    action_callback: callable | None = None,
) -> None:
    """Render a consistent empty state across all pages.

    Args:
        title: The main title/headline for the empty state
        description: Detailed explanation of why this state exists
        icon: Optional emoji or icon to display (default: empty mailbox)
        action_text: Optional text for a call-to-action button
        action_callback: Optional callback function for the action button
    """
    st.markdown(
        f"""
        <div style="
            text-align: center;
            padding: {Theme.spacing.CARD_PADDING_COMFORTABLE}px;
            background: {Theme.color.BACKGROUND_SURFACE};
            border: 1px solid {Theme.color.BORDER};
            border-radius: 8px;
            margin: {Theme.spacing.SECTION_GAP}px 0;
        ">
            <div style="font-size: 48px; margin-bottom: 16px;">{icon}</div>
            <h3 style="
                color: {Theme.color.TEXT_PRIMARY};
                font-size: {Theme.typography.SECTION_HEADER_SIZE}px;
                font-weight: {Theme.typography.SECTION_HEADER_WEIGHT};
                margin: 0 0 8px 0;
            ">{title}</h3>
            <p style="
                color: {Theme.color.TEXT_SECONDARY};
                font-size: {Theme.typography.BODY_SIZE}px;
                margin: 0;
            ">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if action_text and action_callback:
        if st.button(action_text, type="primary"):
            action_callback()


def loading_state(message: str, elapsed: float | None = None) -> None:
    """Render a consistent loading state with progress indication.

    Args:
        message: The loading message to display
        elapsed: Optional elapsed time in seconds for long operations
    """
    time_text = f" ({elapsed:.1f}s)" if elapsed else ""
    st.markdown(
        f"""
        <div style="
            padding: {Theme.spacing.CARD_PADDING_COMPACT}px;
            background: {Theme.color.BACKGROUND_SURFACE};
            border: 1px solid {Theme.color.BORDER};
            border-radius: 8px;
            margin: {Theme.spacing.SECTION_GAP}px 0;
            display: flex;
            align-items: center;
            gap: 12px;
        ">
            <div style="
                width: 20px;
                height: 20px;
                border: 2px solid {Theme.color.ACCENT_PRIMARY};
                border-top-color: transparent;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            "></div>
            <span style="
                color: {Theme.color.TEXT_PRIMARY};
                font-size: {Theme.typography.BODY_SIZE}px;
            ">{message}{time_text}</span>
        </div>
        <style>
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def error_state(
    message: str,
    recovery_hint: str | None = None,
    error_code: str | None = None,
) -> None:
    """Render a consistent error state with recovery guidance.

    Args:
        message: The main error message
        recovery_hint: Optional hint on how to recover from the error
        error_code: Optional error code for debugging
    """
    code_text = f" <code style='background: {Theme.color.BACKGROUND_ELEVATED}; padding: 2px 6px; border-radius: 4px;'>[{error_code}]</code>" if error_code else ""
    hint_text = f"\n\n**Recovery:** {recovery_hint}" if recovery_hint else ""

    st.error(f"{code_text} {message}{hint_text}")


def success_state(message: str, details: str | None = None) -> None:
    """Render a consistent success state.

    Args:
        message: The success message
        details: Optional additional details
    """
    if details:
        st.success(f"{message}\n\n{details}")
    else:
        st.success(message)


def warning_state(message: str, details: str | None = None) -> None:
    """Render a consistent warning state.

    Args:
        message: The warning message
        details: Optional additional details
    """
    if details:
        st.warning(f"{message}\n\n{details}")
    else:
        st.warning(message)