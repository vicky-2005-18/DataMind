"""Badge and pill components."""

from html import escape

from datamind.ui.components.styles import PILL_CLASSES, PillVariant


def pill_html(label: str, variant: PillVariant = "primary") -> str:
    """Return an accessible pill badge. Color is always paired with a text label."""
    css = PILL_CLASSES.get(variant, PILL_CLASSES["primary"])
    return f'<span class="{css}">{escape(label)}</span>'


def render_pill(label: str, variant: PillVariant = "primary") -> None:
    """Render a labeled status or category pill."""
    import streamlit as st

    st.markdown(pill_html(label, variant), unsafe_allow_html=True)


def render_rank_medal(rank: int) -> str:
    """Return a medal badge for the top-3 ranked rows; higher ranks get a neutral pill."""
    medals = {
        1: ("dm-medal-gold", "Rank 1"),
        2: ("dm-medal-silver", "Rank 2"),
        3: ("dm-medal-bronze", "Rank 3"),
    }
    if rank in medals:
        css, label = medals[rank]
        return f'<span class="dm-medal {css}">{escape(label)}</span>'
    return pill_html(f"Rank {rank}", "muted")
