"""Form and state components."""

from typing import Optional

from datamind.contracts import ServiceError

import streamlit as st


def render_service_error(error: Exception) -> None:
    """Render a standardized error callout with actionable guidance."""
    if isinstance(error, ServiceError):
        st.error(f"**[{error.code.value}]** {error.user_message}")
        if error.field:
            st.caption(f"Affects field: `{error.field}`")
    else:
        st.error(f"**An unexpected error occurred:** {error}")


def render_loading_state(message: str, elapsed: Optional[float] = None) -> None:
    """Render a standardized loading state with optional elapsed time display.

    Args:
        message: The loading message to display
        elapsed: Optional elapsed time in seconds to show progress
    """
    if elapsed is not None:
        elapsed_str = f" ({elapsed:.1f}s elapsed)" if elapsed >= 1.0 else ""
        st.info(f"⏳ **{message}**{elapsed_str}")
    else:
        st.info(f"⏳ **{message}**")


def render_error_state(message: str, recovery_hint: Optional[str] = None) -> None:
    """Render a standardized error state for non-service errors.

    Args:
        message: The error message to display
        recovery_hint: Optional hint for how to recover from the error
    """
    st.error(f"**{message}**")
    if recovery_hint:
        st.caption(f"💡 {recovery_hint}")
