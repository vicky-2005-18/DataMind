"""Table and visualization components."""

from html import escape
from typing import Dict, List

from datamind.contracts import MetricScope, TrialResult
from datamind.ui.components.badges import pill_html

import streamlit as st


def render_split_bar(dev_count: int, holdout_count: int) -> None:
    """Render the development/holdout partition visualizer with real row counts."""
    total = dev_count + holdout_count
    if total <= 0:
        return
    dev_pct = round(dev_count / total * 100, 1)
    holdout_pct = 100 - dev_pct
    st.markdown(
        f'<div><div class="dm-split-bar" role="img" '
        f'aria-label="Partition: {dev_count:,} development rows and {holdout_count:,} holdout rows">'
        f'<div class="dm-split-seg dm-split-dev" style="flex-basis: {dev_pct}%;"><span>Development</span>'
        f"<small>{dev_count:,} · {dev_pct}%</small></div>"
        f'<div class="dm-split-seg dm-split-holdout" style="flex-basis: {holdout_pct}%;"><span>Holdout</span>'
        f"<small>{holdout_count:,} · {holdout_pct:.1f}%</small></div></div>"
        f'<p class="dm-caption" style="margin: 0.4rem 0 0;">Development rows drive CV and EDA. '
        f"Holdout rows stay untouched until finalization.</p></div>",
        unsafe_allow_html=True,
    )


def render_activity_timeline(entries: List[Dict[str, str]]) -> None:
    """Render an activity horizon; each entry has title, when, detail, and pill_label/pill_variant."""
    items: List[str] = []
    for entry in entries:
        variant = entry.get("pill_variant", "primary")
        pill = pill_html(entry["pill_label"], variant) if entry.get("pill_label") else ""
        items.append(
            f'<div class="dm-timeline-item" role="list-item">'
            f'<div class="dm-timeline-head"><span class="dm-timeline-title">{escape(entry["title"])}</span>'
            f'<span class="dm-timeline-when">{escape(entry["when"])}</span></div>'
            f'<div style="margin-top: 0.25rem;">{pill}</div>'
            f'<div class="dm-timeline-detail">{escape(entry.get("detail", ""))}</div></div>'
        )
    st.markdown(f'<div class="dm-timeline">{"".join(items)}</div>', unsafe_allow_html=True)


def render_fold_ticker(trial: TrialResult, primary_metric: str) -> None:
    """Render fold-by-fold primary metric chips from real stored per-fold metrics."""
    fold_values = [
        record.value
        for record in trial.metrics
        if record.scope == MetricScope.CV_FOLD and record.name == primary_metric
    ]
    if not fold_values:
        return
    chips = " ".join(
        f'<span class="dm-fold-chip">F{i} {value:.4f}</span>' for i, value in enumerate(fold_values)
    )
    mean = trial.primary_cv_mean
    std = trial.primary_cv_std
    summary = (
        f'<span class="dm-fold-chip" style="border-color: var(--dm-primary);">'
        f"mean {mean:.4f} ± {std:.4f}</span>"
        if mean is not None and std is not None
        else ""
    )
    st.markdown(
        f'<div style="display: flex; gap: 0.45rem; flex-wrap: wrap;">{chips} {summary}</div>',
        unsafe_allow_html=True,
    )


def render_probability_bars(classes: List[str], probabilities: List[float]) -> None:
    """Render predicted-class probability bars for one row (classification only)."""
    if not classes or not probabilities:
        return
    rows = "".join(
        f'<div class="dm-conf-row"><span class="dm-conf-label">{escape(label)}</span>'
        f'<span class="dm-conf-track"><span class="dm-conf-fill" style="width: {max(0.0, min(1.0, prob)) * 100:.2f}%;"></span></span>'
        f'<span class="dm-conf-value">{prob:.1%}</span></div>'
        for label, prob in zip(classes, probabilities)
    )
    st.markdown(
        f'<div aria-label="Predicted class probabilities">{rows}</div>', unsafe_allow_html=True
    )
