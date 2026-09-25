"""Reusable Streamlit UI components and layout helpers for DataMind.

Phase 1 (Foundation & Theming): design tokens, dark/light contrast,
brand header, pill badges, and bento cards.
"""

from __future__ import annotations

from html import escape
from typing import Dict, List, Literal, Optional, Tuple

import streamlit as st

from datamind.contracts import MetricScope, ProjectSummary, ServiceError, TrialResult
from datamind.ui.charts.plotly_theme import apply_shared_theme

PillVariant = Literal["primary", "cyan", "success", "amber", "rose", "muted"]
BentoSpan = Literal["1x1", "2x1", "2x2"]

PILL_CLASSES: dict[str, str] = {
    "primary": "dm-pill dm-pill-primary",
    "cyan": "dm-pill dm-pill-cyan",
    "success": "dm-pill dm-pill-success",
    "amber": "dm-pill dm-pill-amber",
    "rose": "dm-pill dm-pill-rose",
    "muted": "dm-pill dm-pill-muted",
}

GLOBAL_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

:root {
  --dm-font-sans: 'Plus Jakarta Sans', Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --dm-font-body: Inter, 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --dm-font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

  --dm-canvas: #0b0f19;
  --dm-surface-primary: #111827;
  --dm-surface-elevated: #1e293b;
  --dm-surface-glass: rgba(17, 24, 39, 0.75);
  --dm-surface: var(--dm-surface-primary);
  --dm-surface-subtle: #0f172a;

  --dm-primary: #6366f1;
  --dm-primary-hover: #4f46e5;
  --dm-primary-glow: rgba(99, 102, 241, 0.25);
  --dm-accent-cyan: #06b6d4;
  --dm-accent-cyan-glow: rgba(6, 182, 212, 0.2);
  --dm-accent-emerald: #10b981;
  --dm-accent-amber: #f59e0b;
  --dm-accent-rose: #f43f5e;

  --dm-border-subtle: rgba(255, 255, 255, 0.08);
  --dm-border-focus: rgba(99, 102, 241, 0.6);
  --dm-border: var(--dm-border-subtle);
  --dm-border-glow: linear-gradient(135deg, rgba(99, 102, 241, 0.3), rgba(6, 182, 212, 0.15), transparent);

  --dm-text-strong: #f9fafb;
  --dm-text-muted: #94a3b8;
  --dm-text-dim: #64748b;
  --dm-text: var(--dm-text-strong);
  --dm-muted: var(--dm-text-muted);

  --dm-success: var(--dm-accent-emerald);
  --dm-warning: var(--dm-accent-amber);
  --dm-error: var(--dm-accent-rose);

  --dm-radius-sm: 8px;
  --dm-radius-md: 14px;
  --dm-radius-lg: 20px;
  --dm-space-1: 8px;
  --dm-space-2: 16px;
  --dm-space-3: 24px;
  --dm-shadow-bento: 0 4px 20px -2px rgba(0, 0, 0, 0.4), 0 0 0 1px var(--dm-border-subtle);
  --dm-shadow-glow: 0 0 25px -5px rgba(99, 102, 241, 0.35);
  --dm-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.28);
}

/* High-clarity light theme when Streamlit is not in dark color-scheme */
html[data-theme="light"],
html:has(body[style*="color-scheme: light"]) {
  --dm-canvas: #f8fafc;
  --dm-surface-primary: #ffffff;
  --dm-surface-elevated: #f8fafc;
  --dm-surface-glass: rgba(255, 255, 255, 0.78);
  --dm-surface: #ffffff;
  --dm-surface-subtle: #f1f5f9;
  --dm-border-subtle: #e2e8f0;
  --dm-text-strong: #0f172a;
  --dm-text-muted: #64748b;
  --dm-text-dim: #94a3b8;
  --dm-shadow-bento: 0 4px 16px -2px rgba(15, 23, 42, 0.07), 0 0 0 1px rgba(226, 232, 240, 0.8);
  --dm-shadow-glow: 0 0 20px -3px rgba(99, 102, 241, 0.25);
  --dm-shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.06);
}

/* Global font: explicitly exclude SVG elements inside Plotly charts so our
   font rules never interfere with Plotly's internal text-metric calculations. */
html, body, [class*="css"]:not(svg):not(svg *) {
  font-family: var(--dm-font-body);
}

/* Additional protection: Force Plotly SVG text to use system fonts only */
svg text, .plotly svg text, [class*="plotly"] text, 
.g svg text, .js-plotly-plot text, .plotly .tooltip text {
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

/* Fix tooltip positioning: ensure proper line-height without breaking Plotly's transforms */
.plotly .hovertext text, .plotly .hoverlayer text {
  line-height: 1.3 !important;
  dominant-baseline: auto !important;
  text-anchor: start !important;
}

/* Ensure tooltip background box contains the text properly */
.plotly .hovertext rect {
  fill-opacity: 1 !important;
}

/* Ensure proper spacing between tooltip text lines */
.plotly .hovertext tspan {
  dominant-baseline: auto !important;
}

/* Ensure Plotly containers don't interfere with tooltip positioning */
.js-plotly-plot, .plotly, .js-plotly-plot .plotly, 
[data-testid="stPlotlyChart"] {
  position: relative !important;
  transform: none !important;
  overflow: visible !important;
}

/* Ensure the hover layer can position correctly */
.plotly .hoverlayer {
  position: absolute !important;
  pointer-events: none !important;
  transform: none !important;
  z-index: 1000 !important;
}

/* Ensure tooltip text is fully visible and properly positioned */
.plotly .hovertext {
  opacity: 1 !important;
  white-space: normal !important;
  max-width: 300px !important;
}

/* Improve chart styling for professional appearance */
/* NOTE: overflow: visible is critical for Plotly tooltip positioning */
.stPlotlyChart {
  border-radius: var(--dm-radius-md);
  overflow: visible;
}

h1, h2, h3, h4, .dm-brand-name, .dm-bento-title, .dm-workflow-step-name {
  font-family: var(--dm-font-sans);
  letter-spacing: -0.03em;
}

code, kbd, samp, pre, .dm-metric, .dm-context-value {
  font-family: var(--dm-font-mono) !important;
  font-variant-numeric: tabular-nums;
}

.stApp {
  background: var(--dm-canvas);
  color: var(--dm-text-strong);
}

[data-testid="stMainBlockContainer"] {
  padding-top: var(--dm-space-3);
  padding-bottom: 4.5rem;
  max-width: 1440px;
}

[data-testid="stSidebar"] {
  background: var(--dm-surface-primary);
  border-right: 1px solid var(--dm-border-subtle);
}

[data-testid="stSidebarContent"] {
  padding: 0.85rem;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  gap: 0.65rem;
}

[data-testid="stSidebar"] .stRadio > label {
  color: var(--dm-text-muted);
  font-size: 0.74rem;
  font-weight: 750;
  letter-spacing: 0.09em;
  text-transform: uppercase;
}

[data-testid="stSidebar"] .stRadio [role="radiogroup"] {
  gap: 0.25rem;
}

[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
  border-radius: var(--dm-radius-sm);
  padding: 0.5rem 0.65rem;
  font-weight: 550;
  cursor: pointer;
  transition: background-color 180ms ease, color 180ms ease, transform 180ms cubic-bezier(0.16, 1, 0.3, 1);
}

[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
  background: color-mix(in srgb, var(--dm-primary) 12%, transparent);
  color: var(--dm-primary);
  transform: translateX(2px);
}

[data-testid="stForm"],
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--dm-surface-primary);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-lg);
  box-shadow: var(--dm-shadow-bento);
  transition: box-shadow 200ms ease, border-color 200ms ease, transform 200ms ease;
}

[data-testid="stForm"]:hover,
[data-testid="stVerticalBlockBorderWrapper"]:hover {
  box-shadow: var(--dm-shadow-glow), var(--dm-shadow-bento);
  border-color: color-mix(in srgb, var(--dm-primary) 40%, var(--dm-border-subtle));
}

.dm-bento-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--dm-space-2);
  margin: 0 0 var(--dm-space-3);
}

.dm-bento-card {
  background: var(--dm-surface-primary);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-lg);
  box-shadow: var(--dm-shadow-bento);
  padding: var(--dm-space-2);
  position: relative;
  overflow: hidden;
  transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 200ms ease;
}

.dm-bento-card::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  background: var(--dm-border-glow);
  opacity: 0.35;
  mask: linear-gradient(#000, #000) content-box, linear-gradient(#000, #000);
  mask-composite: exclude;
  padding: 1px;
}

.dm-bento-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--dm-shadow-glow);
}

.dm-bento-1x1 { grid-column: span 1; grid-row: span 1; }
.dm-bento-2x1 { grid-column: span 2; grid-row: span 1; }
.dm-bento-2x2 { grid-column: span 2; grid-row: span 2; }

.dm-bento-card.dm-bento-hero .dm-bento-title {
  font-size: 1.4rem;
  letter-spacing: -0.03em;
}

.dm-bento-card.dm-bento-hero .dm-bento-body {
  font-size: 0.95rem;
}

.dm-hero-stats {
  display: flex;
  gap: 1.75rem;
  flex-wrap: wrap;
  margin-top: 0.85rem;
}

.dm-hero-stat {
  display: inline-flex;
  flex-direction: column;
}

.dm-hero-stat-value {
  font-family: var(--dm-font-mono);
  font-size: 1.45rem;
  font-weight: 800;
  color: var(--dm-text-strong);
  font-variant-numeric: tabular-nums;
}

.dm-hero-stat-label {
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.09em;
  color: var(--dm-text-muted);
  font-weight: 750;
  margin-top: 0.1rem;
}

.dm-split-bar {
  display: flex;
  height: 2.75rem;
  border-radius: var(--dm-radius-sm);
  overflow: hidden;
  border: 1px solid var(--dm-border-subtle);
  box-shadow: var(--dm-shadow-sm);
}

.dm-split-seg {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  font-size: 0.82rem;
  font-weight: 700;
  min-width: 0;
  transition: flex-basis 200ms ease;
  padding: 0 0.4rem;
}

.dm-split-seg small {
  font-family: var(--dm-font-mono);
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}

.dm-split-dev {
  background: color-mix(in srgb, var(--dm-primary) 88%, #000);
  color: #ffffff;
}

.dm-split-holdout {
  background: color-mix(in srgb, var(--dm-accent-cyan) 30%, var(--dm-surface-primary));
  color: var(--dm-text-strong);
}

.dm-timeline {
  border-left: 2px solid color-mix(in srgb, var(--dm-primary) 40%, transparent);
  margin: 0.4rem 0 0 0.55rem;
  padding-left: 1.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.dm-timeline-item { position: relative; }

.dm-timeline-item::before {
  content: "";
  position: absolute;
  left: -1.38rem;
  top: 0.4rem;
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  background: var(--dm-primary);
  box-shadow: 0 0 8px var(--dm-primary-glow);
}

.dm-timeline-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.dm-timeline-title {
  font-weight: 750;
  color: var(--dm-text-strong);
  font-size: 0.92rem;
}

.dm-timeline-when {
  font-family: var(--dm-font-mono);
  color: var(--dm-text-dim);
  font-size: 0.72rem;
  white-space: nowrap;
}

.dm-timeline-detail {
  color: var(--dm-text-muted);
  font-size: 0.8rem;
  margin-top: 0.2rem;
}

.dm-fold-chip {
  display: inline-block;
  font-family: var(--dm-font-mono);
  font-size: 0.74rem;
  background: var(--dm-surface-elevated);
  border: 1px solid var(--dm-border-subtle);
  border-radius: 6px;
  padding: 0.22rem 0.55rem;
  color: var(--dm-text-strong);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.dm-medal {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.02em;
}

.dm-medal-gold {
  background: rgba(251, 191, 36, 0.16);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.5);
}

.dm-medal-silver {
  background: rgba(203, 213, 225, 0.16);
  color: #cbd5e1;
  border: 1px solid rgba(203, 213, 225, 0.45);
}

.dm-medal-bronze {
  background: rgba(217, 119, 6, 0.18);
  color: #fdba74;
  border: 1px solid rgba(217, 119, 6, 0.5);
}

html[data-theme="light"] .dm-medal-gold,
html:has(body[style*="color-scheme: light"]) .dm-medal-gold {
  background: #fef3c7;
  color: #92400e;
}

html[data-theme="light"] .dm-medal-silver,
html:has(body[style*="color-scheme: light"]) .dm-medal-silver {
  background: #f1f5f9;
  color: #475569;
}

html[data-theme="light"] .dm-medal-bronze,
html:has(body[style*="color-scheme: light"]) .dm-medal-bronze {
  background: #ffedd5;
  color: #9a3412;
}

.dm-conf-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0.3rem 0;
}

.dm-conf-label {
  width: 38%;
  font-size: 0.8rem;
  color: var(--dm-text-muted);
  overflow-wrap: anywhere;
}

.dm-conf-track {
  flex: 1;
  height: 0.72rem;
  background: var(--dm-surface-subtle);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid var(--dm-border-subtle);
}

.dm-conf-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--dm-primary), var(--dm-accent-cyan));
  border-radius: 999px;
}

.dm-conf-value {
  font-family: var(--dm-font-mono);
  font-size: 0.78rem;
  color: var(--dm-text-strong);
  width: 3.4rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

[data-testid="stFileUploaderDropzone"] {
  background: var(--dm-surface-glass);
  backdrop-filter: blur(12px);
  border: 1.5px dashed color-mix(in srgb, var(--dm-primary) 45%, var(--dm-border-subtle)) !important;
  border-radius: var(--dm-radius-lg) !important;
  transition: border-color 200ms ease, box-shadow 200ms ease;
}

[data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--dm-primary) !important;
  box-shadow: var(--dm-shadow-glow);
}

.dm-bento-kicker {
  color: var(--dm-primary);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin: 0 0 6px;
}

.dm-bento-title {
  color: var(--dm-text-strong);
  font-size: 1.05rem;
  font-weight: 750;
  margin: 0 0 8px;
  line-height: 1.25;
}

.dm-bento-body {
  color: var(--dm-text-muted);
  font-size: 0.9rem;
  line-height: 1.55;
  margin: 0;
}

.dm-bento-footer {
  margin-top: 12px;
  color: var(--dm-text-dim);
  font-size: 0.75rem;
}

[data-testid="stMetric"] {
  background: var(--dm-surface-primary);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-md);
  box-shadow: var(--dm-shadow-bento);
  padding: 1.1rem 1.25rem;
  position: relative;
  overflow: hidden;
  transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 200ms ease;
}

[data-testid="stMetric"]:hover {
  transform: translateY(-2px);
  box-shadow: var(--dm-shadow-glow), var(--dm-shadow-bento);
}

[data-testid="stMetricLabel"] {
  font-size: 0.8rem !important;
  font-weight: 700 !important;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--dm-text-muted) !important;
}

[data-testid="stMetricValue"] {
  font-family: var(--dm-font-mono) !important;
  font-size: 1.85rem !important;
  font-weight: 800 !important;
  letter-spacing: -0.03em !important;
  color: var(--dm-text-strong) !important;
  font-variant-numeric: tabular-nums;
}

[data-baseweb="input"] > div,
[data-baseweb="select"] > div,
textarea {
  border-radius: var(--dm-radius-sm) !important;
  border-color: var(--dm-border-subtle) !important;
  transition: border-color 180ms ease, box-shadow 180ms ease !important;
}

[data-baseweb="input"] > div:focus-within,
[data-baseweb="select"] > div:focus-within,
textarea:focus {
  border-color: var(--dm-primary) !important;
  box-shadow: 0 0 0 3px var(--dm-primary-glow) !important;
}

/* ── Fix: prevent floating/animating label on hover & focus ── */
/* Streamlit's BaseWeb widgets animate the label upward on focus by default.
   We lock the label to its static position above the widget at all times.
   NOTE: These rules are scoped to form-control/widget labels only — they do
   NOT touch SVG text elements or Plotly chart tooltips. */
[data-baseweb="form-control"] > label,
[data-baseweb="form-control"] label,
.stSelectbox label,
.stTextInput label,
.stTextArea label,
.stNumberInput label,
.stMultiSelect label,
.stDateInput label,
.stTimeInput label,
.stSlider label,
.stFileUploader label {
  position: static !important;
  transform: none !important;
  transition: none !important;
  top: auto !important;
  left: auto !important;
  font-size: 0.875rem !important;
  color: var(--dm-text-muted) !important;
  font-weight: 500 !important;
  margin-bottom: 0.25rem !important;
  display: block !important;
}

/* Also target BaseWeb's internal label container */
[data-baseweb="select"] [data-baseweb="form-control-label"],
[data-baseweb="input"] [data-baseweb="form-control-label"] {
  position: static !important;
  transform: none !important;
  transition: none !important;
  animation: none !important;
}

/* Prevent the label from moving on :focus-within */
[data-baseweb="form-control"]:focus-within > label,
[data-baseweb="form-control"]:hover > label {
  position: static !important;
  transform: none !important;
  top: auto !important;
  left: auto !important;
  font-size: 0.875rem !important;
}


.stButton > button,
.stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button,
.stRadio label,
.stCheckbox label,
[data-testid="stMetric"] {
  cursor: pointer;
}

.stButton > button,
.stDownloadButton > button,
[data-testid="stFormSubmitButton"] > button {
  min-height: 2.65rem;
  border-radius: var(--dm-radius-sm);
  font-weight: 650;
  letter-spacing: -0.01em;
  transition: transform 180ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 180ms ease, background 180ms ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.28);
}

.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, var(--dm-primary), var(--dm-primary-hover));
  border: none;
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.stButton > button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primary"]:hover {
  background: linear-gradient(135deg, var(--dm-primary-hover), #4338ca);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.45);
  transform: translateY(-1.5px);
}

button:focus-visible,
input:focus-visible,
textarea:focus-visible,
select:focus-visible,
[role="radio"]:focus-visible,
[role="combobox"]:focus-visible,
a:focus-visible {
  outline: 3px solid rgba(99, 102, 241, 0.4) !important;
  outline-offset: 2px !important;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
  background: var(--dm-surface-primary);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-md);
  box-shadow: var(--dm-shadow-sm);
  overflow: hidden;
}

[data-testid="stExpander"] {
  background: var(--dm-surface-primary);
  border-color: var(--dm-border-subtle);
  border-radius: var(--dm-radius-md);
  box-shadow: var(--dm-shadow-sm);
}

hr {
  border-color: var(--dm-border-subtle) !important;
}

.dm-eyebrow {
  color: var(--dm-primary);
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  margin: 0 0 0.35rem;
  text-transform: uppercase;
}

h1 {
  color: var(--dm-text-strong);
  font-weight: 800 !important;
  letter-spacing: -0.035em !important;
  line-height: 1.12 !important;
}

.dm-page-subtitle {
  color: var(--dm-text-muted);
  font-size: 1.02rem;
  line-height: 1.55;
  margin: -0.2rem 0 0;
  max-width: 52rem;
}

.dm-rule {
  background: linear-gradient(90deg, var(--dm-primary), var(--dm-accent-cyan), transparent);
  border-radius: 999px;
  height: 3px;
  margin: 1rem 0 1.5rem;
  width: 8rem;
}

.dm-brand {
  padding: 0.4rem 0 0.2rem;
}

.dm-brand-mark {
  align-items: center;
  background: linear-gradient(135deg, var(--dm-primary), var(--dm-accent-cyan));
  border-radius: 0.8rem;
  color: white;
  display: inline-flex;
  font-size: 1.05rem;
  font-weight: 800;
  height: 2.6rem;
  justify-content: center;
  margin-right: 0.65rem;
  width: 2.6rem;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.dm-brand-name {
  color: var(--dm-text-strong);
  font-size: 1.3rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.dm-brand-copy {
  color: var(--dm-text-muted);
  font-size: 0.78rem;
  margin: 0.35rem 0 0;
}

.dm-stage {
  color: var(--dm-text-muted);
  font-size: 0.72rem;
  font-weight: 750;
  letter-spacing: 0.08em;
  margin: 0.65rem 0 0.15rem;
  text-transform: uppercase;
}

.dm-context {
  background: var(--dm-surface-glass);
  backdrop-filter: blur(12px);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-md);
  padding: 0.8rem;
  box-shadow: var(--dm-shadow-sm);
}

.dm-context-label {
  color: var(--dm-text-muted);
  font-size: 0.68rem;
  font-weight: 750;
  letter-spacing: 0.09em;
  margin: 0;
  text-transform: uppercase;
}

.dm-context-value {
  color: var(--dm-text-strong);
  font-size: 0.88rem;
  font-weight: 700;
  margin: 0.2rem 0 0;
  overflow-wrap: anywhere;
}

.dm-runtime {
  align-items: center;
  color: var(--dm-text-muted);
  display: flex;
  font-size: 0.78rem;
  gap: 0.45rem;
}

.dm-runtime-dot {
  background: var(--dm-accent-emerald);
  border-radius: 50%;
  height: 0.55rem;
  width: 0.55rem;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  animation: dm-pulse 2s infinite ease-in-out;
}

@keyframes dm-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.15); opacity: 0.6; }
}

.dm-status {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.dm-status-dot {
  border-radius: 50%;
  height: 0.5rem;
  width: 0.5rem;
}

.dm-status-live .dm-status-dot {
  background: var(--dm-accent-emerald);
  animation: dm-pulse 2s infinite ease-in-out;
}

.dm-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.dm-pill-primary {
  background: rgba(99, 102, 241, 0.16);
  color: #c7d2fe;
  border: 1px solid rgba(99, 102, 241, 0.35);
}

.dm-pill-cyan {
  background: rgba(6, 182, 212, 0.14);
  color: #67e8f9;
  border: 1px solid rgba(6, 182, 212, 0.35);
}

.dm-pill-success {
  background: rgba(16, 185, 129, 0.14);
  color: #6ee7b7;
  border: 1px solid rgba(16, 185, 129, 0.35);
}

.dm-pill-amber {
  background: rgba(245, 158, 11, 0.16);
  color: #fcd34d;
  border: 1px solid rgba(245, 158, 11, 0.35);
}

.dm-pill-rose {
  background: rgba(244, 63, 94, 0.16);
  color: #fda4af;
  border: 1px solid rgba(244, 63, 94, 0.35);
}

.dm-pill-muted {
  background: rgba(148, 163, 184, 0.12);
  color: var(--dm-text-muted);
  border: 1px solid var(--dm-border-subtle);
}

html[data-theme="light"] .dm-pill-primary,
html:has(body[style*="color-scheme: light"]) .dm-pill-primary {
  background: #eef2ff;
  color: var(--dm-primary);
}

html[data-theme="light"] .dm-pill-cyan,
html:has(body[style*="color-scheme: light"]) .dm-pill-cyan {
  background: #ecfeff;
  color: #0e7490;
}

html[data-theme="light"] .dm-pill-success,
html:has(body[style*="color-scheme: light"]) .dm-pill-success {
  background: #ecfdf5;
  color: #047857;
}

.dm-workflow-rail {
  display: flex;
  gap: 0.75rem;
  margin: 1.25rem 0 1.5rem;
  overflow-x: auto;
  padding-bottom: 0.35rem;
}

.dm-workflow-card {
  flex: 1;
  min-width: 140px;
  background: var(--dm-surface-primary);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-md);
  padding: 0.85rem 1rem;
  box-shadow: var(--dm-shadow-sm);
  cursor: pointer;
  transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1), box-shadow 200ms ease;
}

.dm-workflow-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--dm-shadow-bento);
}

.dm-workflow-card.active {
  border-color: var(--dm-primary);
  background: linear-gradient(180deg, var(--dm-surface-primary) 0%, color-mix(in srgb, var(--dm-primary) 12%, var(--dm-surface-primary)) 100%);
  box-shadow: var(--dm-shadow-glow);
}

.dm-workflow-step-num {
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--dm-primary);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.dm-workflow-step-name {
  font-size: 0.92rem;
  font-weight: 750;
  color: var(--dm-text-strong);
  margin: 0.15rem 0 0.1rem;
}

.dm-workflow-step-desc {
  font-size: 0.75rem;
  color: var(--dm-text-muted);
  line-height: 1.4;
}

.dm-project-banner {
  background: var(--dm-surface-primary);
  border: 1px solid var(--dm-border-subtle);
  border-left: 4px solid var(--dm-primary);
  border-radius: var(--dm-radius-md);
  padding: 0.85rem 1.15rem;
  margin-bottom: 1.25rem;
  box-shadow: var(--dm-shadow-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.dm-project-id {
  font-family: var(--dm-font-mono);
  font-size: 0.78rem;
  color: var(--dm-text-muted);
  background: var(--dm-surface-elevated);
  padding: 0.25rem 0.55rem;
  border-radius: 0.4rem;
  border: 1px solid var(--dm-border-subtle);
}

/* Additional breakpoint for narrow laptops as per UI/UX enhancement plan */
@media (max-width: 1280px) {
  [data-testid="stMainBlockContainer"] { max-width: 1200px; }
}

@media (max-width: 1024px) {
  [data-testid="stMainBlockContainer"] { padding-left: 1.5rem; padding-right: 1.5rem; }
  .dm-bento-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dm-bento-2x1, .dm-bento-2x2 { grid-column: span 2; }
}

@media (max-width: 768px) {
  [data-testid="stMainBlockContainer"] { padding-left: 1rem; padding-right: 1rem; padding-top: 1.25rem; }
  h1 { font-size: 2rem !important; }
  .dm-page-subtitle { font-size: 0.95rem; }
  .dm-bento-grid { grid-template-columns: 1fr; }
  .dm-bento-1x1, .dm-bento-2x1, .dm-bento-2x2 { grid-column: span 1; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stHorizontalBlock"] > [data-testid="column"] { min-width: min(100%, 18rem) !important; flex: 1 1 18rem !important; }
}

@media (max-width: 375px) {
  h1 { font-size: 1.65rem !important; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
  .dm-bento-card:hover,
  [data-testid="stMetric"]:hover,
  .dm-workflow-card:hover {
    transform: none;
  }
}
</style>
"""


def apply_global_styles() -> None:
    """Apply the shared DataMind visual system."""
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)


def pill_html(label: str, variant: PillVariant = "primary") -> str:
    """Return an accessible pill badge. Color is always paired with a text label."""
    css = PILL_CLASSES.get(variant, PILL_CLASSES["primary"])
    return f'<span class="{css}">{escape(label)}</span>'


def render_pill(label: str, variant: PillVariant = "primary") -> None:
    """Render a labeled status or category pill."""
    st.markdown(pill_html(label, variant), unsafe_allow_html=True)


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
        kicker = f'<p class="dm-bento-kicker">{item.get("kicker_html", "")}</p>' if item.get(
            "kicker_html"
        ) else ""
        footer = f'<p class="dm-bento-footer">{item.get("footer_html", "")}</p>' if item.get(
            "footer_html"
        ) else ""
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
        f'<small>{dev_count:,} · {dev_pct}%</small></div>'
        f'<div class="dm-split-seg dm-split-holdout" style="flex-basis: {holdout_pct}%;"><span>Holdout</span>'
        f'<small>{holdout_count:,} · {holdout_pct:.1f}%</small></div></div>'
        f'<p class="dm-caption" style="margin: 0.4rem 0 0;">Development rows drive CV and EDA. '
        f'Holdout rows stay untouched until finalization.</p></div>',
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


def render_rank_medal(rank: int) -> str:
    """Return a medal badge for the top-3 ranked rows; higher ranks get a neutral pill."""
    medals = {1: ("dm-medal-gold", "Rank 1"), 2: ("dm-medal-silver", "Rank 2"), 3: ("dm-medal-bronze", "Rank 3")}
    if rank in medals:
        css, label = medals[rank]
        return f'<span class="dm-medal {css}">{escape(label)}</span>'
    return pill_html(f"Rank {rank}", "muted")


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


def render_header(title: str, subtitle: str) -> None:
    """Render consistent page title, eyebrow, and luminous divider."""
    st.markdown('<p class="dm-eyebrow">DataMind AI Laboratory</p>', unsafe_allow_html=True)
    st.title(title, anchor=False)
    st.markdown(f'<p class="dm-page-subtitle">{escape(subtitle)}</p>', unsafe_allow_html=True)
    st.markdown('<div class="dm-rule" aria-hidden="true"></div>', unsafe_allow_html=True)


def render_workflow_stepper(current_stage: str = "Workspace") -> None:
    """Render an aesthetic 5-stage workflow rail with active stage highlight."""
    stages = [
        ("1", "Workspace", "Home", "Select or initialize your project environment"),
        ("2", "Prepare", "Data", "Profile schemas, check hygiene & create splits"),
        ("3", "Model", "Train", "Run cross-validation & benchmark candidates"),
        ("4", "Deliver", "Inference", "Simulate predictions & export audit bundles"),
        ("5", "Learn", "Studio", "Explore K-Means clusters & algorithm sandboxes"),
    ]
    cols = st.columns(len(stages))
    for col, (num, name, tag, desc) in zip(cols, stages):
        is_active = name.lower() == current_stage.lower()
        active_class = " active" if is_active else ""
        pill = pill_html(tag, "primary" if is_active else "cyan")
        with col:
            st.markdown(
                f"""
                <div class="dm-workflow-card{active_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="dm-workflow-step-num">STAGE 0{escape(num)}</span>
                        {pill}
                    </div>
                    <div class="dm-workflow-step-name">{escape(name)}</div>
                    <div class="dm-workflow-step-desc">{escape(desc)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_active_project_banner(project: Optional[ProjectSummary]) -> None:
    """Render an informative status pill indicating current workspace context."""
    if project:
        desc_str = f" — {escape(project.description)}" if project.description else ""
        active_pill = pill_html("Active", "primary")
        st.markdown(
            f"""
            <div class="dm-project-banner">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    {active_pill}
                    <div>
                        <span style="font-weight: 750; font-size: 1rem; color: var(--dm-text-strong);">{escape(project.name)}</span>
                        <span style="color: var(--dm-text-muted); font-size: 0.85rem;">{desc_str}</span>
                    </div>
                </div>
                <div class="dm-project-id">ID: {escape(project.id[:8])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("**No Active Project Selected.** Please select or create a project on the **Home** page to begin.")


def render_empty_state(
    milestone: str,
    page_name: str,
    description: str,
    next_action: Optional[str] = None,
) -> None:
    """Render an honest empty state for future milestone pages without fake controls."""
    st.subheader(page_name)
    st.markdown(
        f"""
        > **Status: Scheduled for {escape(milestone)}**

        {escape(description)}
        """
    )
    if next_action:
        st.info(f"**Next step:** {next_action}")
    else:
        st.caption("No mock controls or fabricated data are shown here until this milestone is implemented.")


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


def style_plotly_figure(fig, title: Optional[str] = None):
    """Apply the shared DataMind theme to Plotly figures.

    This function now uses the centralized theme system to ensure consistent
    styling and proper tooltip positioning across all charts.

    Args:
        fig: The Plotly figure to style
        title: Optional title to set on the figure

    Returns:
        The themed figure ready for rendering
    """
    return apply_shared_theme(fig, title)
