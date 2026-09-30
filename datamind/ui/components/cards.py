"""Card and grid components."""

from html import escape
from typing import Dict, List, Literal, Optional, Tuple

from datamind.ui.components.styles import BentoSpan

import streamlit as st


def render_bento_card(
    title: str,
    body: str,
    *,
    kicker: Optional[str] = None,
    footer: Optional[str] = None,
    span: BentoSpan = "1x1",
) -> None:
    """Render a reusable bento surface used as the Phase 1 card primitive."""
    # Single-line HTML: multi-line templates get split into escaped code blocks by the
    # markdown parser whenever an optional interpolation leaves a whitespace-only line.
    kicker_html = f'<p class="dm-bento-kicker">{escape(kicker)}</p>' if kicker else ""
    footer_html = f'<p class="dm-bento-footer">{escape(footer)}</p>' if footer else ""
    st.markdown(
        f'<article class="dm-bento-card dm-bento-{span}">{kicker_html}'
        f'<h3 class="dm-bento-title">{escape(title)}</h3>'
        f'<p class="dm-bento-body">{escape(body)}</p>{footer_html}</article>',
        unsafe_allow_html=True,
    )


def render_bento_grid(items: List[Dict[str, object]]) -> None:
    """Render a bento grid in a single HTML block so spans align to the grid rhythm.

    Each item may provide: ``title``, ``body_html`` (pre-escaped trusted HTML),
    ``kicker``, ``footer_html``, ``span`` (``"1x1"``/``"2x1"``/``"2x2"``),
    and ``hero`` (bool).
    """
    cards: List[str] = []
    for item in items:
        span = str(item.get("span", "1x1"))
        if span not in {"1x1", "2x1", "2x2"}:
            span = "1x1"
        hero = " dm-bento-hero" if item.get("hero") else ""
        kicker = (
            f'<p class="dm-bento-kicker">{item.get("kicker_html", "")}</p>'
            if item.get("kicker_html")
            else ""
        )
        footer = (
            f'<p class="dm-bento-footer">{item.get("footer_html", "")}</p>'
            if item.get("footer_html")
            else ""
        )
        # Compact single-line markup so the markdown parser keeps the whole grid as
        # one raw HTML block (indented multi-line templates degrade into code blocks).
        cards.append(
            f'<article class="dm-bento-card dm-bento-{span}{hero}">{kicker}'
            f'<h3 class="dm-bento-title">{escape(str(item.get("title", "")))}</h3>'
            f'<div class="dm-bento-body">{item.get("body_html", "")}</div>{footer}</article>'
        )
    st.markdown(
        f'<div class="dm-bento-grid" role="list">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_hero_stats(stats: List[Tuple[str, str]]) -> str:
    """Return hero stat markup; each tuple is (value, label). Values must be pre-escaped."""
    cells = "".join(
        f'<div class="dm-hero-stat"><span class="dm-hero-stat-value">{value}</span>'
        f'<span class="dm-hero-stat-label">{escape(label)}</span></div>'
        for value, label in stats
    )
    return f'<div class="dm-hero-stats">{cells}</div>'
