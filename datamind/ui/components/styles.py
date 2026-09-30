"""Global styles and theming for DataMind UI."""

from typing import Literal

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

h1, h2, h3, h4, h5, h6 {
  font-family: var(--dm-font-sans);
  font-weight: 700;
  letter-spacing: -0.025em;
}

code, pre, [class*="code"] {
  font-family: var(--dm-font-mono);
}

/* Custom scrollbars */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: var(--dm-surface-subtle);
}
::-webkit-scrollbar-thumb {
  background: var(--dm-border-subtle);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--dm-text-dim);
}

/* DataMind Design System - Phase 1 Components */
.dm-pill {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.65rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  text-transform: uppercase;
  white-space: nowrap;
}

.dm-pill-primary {
  background: var(--dm-primary);
  color: white;
  box-shadow: 0 0 12px var(--dm-primary-glow);
}

.dm-pill-cyan {
  background: var(--dm-accent-cyan);
  color: white;
  box-shadow: 0 0 12px var(--dm-accent-cyan-glow);
}

.dm-pill-success {
  background: var(--dm-accent-emerald);
  color: white;
}

.dm-pill-amber {
  background: var(--dm-accent-amber);
  color: #1a1a1a;
}

.dm-pill-rose {
  background: var(--dm-accent-rose);
  color: white;
}

.dm-pill-muted {
  background: var(--dm-border-subtle);
  color: var(--dm-text-muted);
}

.dm-bento-card {
  background: var(--dm-surface-elevated);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-md);
  padding: 1.25rem;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: var(--dm-shadow-bento);
}

.dm-bento-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--dm-shadow-glow);
  border-color: var(--dm-border-focus);
}

.dm-bento-kicker {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--dm-accent-cyan);
  margin: 0 0 0.5rem 0;
}

.dm-bento-title {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: var(--dm-text-strong);
}

.dm-bento-body {
  font-size: 0.9rem;
  color: var(--dm-text-muted);
  line-height: 1.5;
  margin: 0 0 0.75rem 0;
}

.dm-bento-footer {
  font-size: 0.8rem;
  color: var(--dm-text-dim);
  margin: 0.5rem 0 0 0;
}

.dm-bento-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin: 1rem 0;
}

.dm-bento-1x1 {
  grid-column: span 1;
}

.dm-bento-2x1 {
  grid-column: span 2;
}

.dm-bento-2x2 {
  grid-column: span 2;
}

.dm-bento-hero {
  background: linear-gradient(135deg, var(--dm-surface-elevated), var(--dm-surface-glass));
}

.dm-hero-stats {
  display: flex;
  gap: 1.5rem;
  margin: 1rem 0;
}

.dm-hero-stat-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--dm-text-strong);
  display: block;
}

.dm-hero-stat-label {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--dm-text-muted);
}

.dm-split-bar {
  display: flex;
  border-radius: var(--dm-radius-sm);
  overflow: hidden;
  margin: 0.5rem 0;
  background: var(--dm-surface-subtle);
}

.dm-split-seg {
  padding: 0.5rem 0.75rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  font-size: 0.8rem;
  font-weight: 600;
}

.dm-split-seg span {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dm-split-dev {
  background: var(--dm-primary);
  color: white;
}

.dm-split-holdout {
  background: var(--dm-accent-amber);
  color: #1a1a1a;
}

.dm-timeline {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin: 1rem 0;
}

.dm-timeline-item {
  padding: 0.75rem;
  background: var(--dm-surface-elevated);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-sm);
}

.dm-timeline-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

.dm-timeline-title {
  font-weight: 600;
  color: var(--dm-text-strong);
}

.dm-timeline-when {
  font-size: 0.75rem;
  color: var(--dm-text-dim);
}

.dm-timeline-detail {
  font-size: 0.85rem;
  color: var(--dm-text-muted);
  margin-top: 0.25rem;
}

.dm-fold-chip {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border: 1px solid var(--dm-border-subtle);
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--dm-font-mono);
  color: var(--dm-text-muted);
}

.dm-medal {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.dm-medal-gold {
  background: linear-gradient(135deg, #ffd700, #ffec8b);
  color: #1a1a1a;
}

.dm-medal-silver {
  background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
  color: #1a1a1a;
}

.dm-medal-bronze {
  background: linear-gradient(135deg, #cd7f32, #d4a574);
  color: white;
}

.dm-conf-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.25rem 0;
}

.dm-conf-label {
  font-size: 0.85rem;
  color: var(--dm-text-muted);
  min-width: 80px;
}

.dm-conf-track {
  flex: 1;
  height: 8px;
  background: var(--dm-surface-subtle);
  border-radius: 4px;
  overflow: hidden;
}

.dm-conf-fill {
  height: 100%;
  background: var(--dm-primary);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.dm-conf-value {
  font-size: 0.85rem;
  font-weight: 600;
  font-family: var(--dm-font-mono);
  color: var(--dm-text-strong);
  min-width: 40px;
  text-align: right;
}

.dm-eyebrow {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--dm-accent-cyan);
  margin: 0 0 0.5rem 0;
}

.dm-page-subtitle {
  font-size: 0.95rem;
  color: var(--dm-text-muted);
  margin: 0 0 1rem 0;
}

.dm-rule {
  height: 2px;
  background: linear-gradient(90deg, var(--dm-primary), var(--dm-accent-cyan), transparent);
  border: none;
  margin: 1.5rem 0;
  border-radius: 1px;
}

.dm-workflow-card {
  background: var(--dm-surface-elevated);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-md);
  padding: 1rem;
  transition: all 0.2s ease;
}

.dm-workflow-card.active {
  border-color: var(--dm-primary);
  box-shadow: 0 0 20px var(--dm-primary-glow);
}

.dm-workflow-card:hover {
  transform: translateY(-2px);
}

.dm-workflow-step-num {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--dm-text-dim);
}

.dm-workflow-step-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--dm-text-strong);
  margin: 0.5rem 0 0.25rem 0;
}

.dm-workflow-step-desc {
  font-size: 0.75rem;
  color: var(--dm-text-muted);
  line-height: 1.4;
}

.dm-project-banner {
  background: var(--dm-surface-elevated);
  border: 1px solid var(--dm-border-subtle);
  border-radius: var(--dm-radius-md);
  padding: 1rem;
  margin: 1rem 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dm-project-id {
  font-size: 0.75rem;
  font-family: var(--dm-font-mono);
  color: var(--dm-text-dim);
}

.dm-caption {
  font-size: 0.8rem;
  color: var(--dm-text-dim);
  font-style: italic;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .dm-bento-grid { grid-template-columns: 1fr; }
  .dm-bento-1x1, .dm-bento-2x1, .dm-bento-2x2 { grid-column: span 1; }
  .dm-hero-stats { flex-direction: column; gap: 0.75rem; }
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

*:focus-visible {
  outline: 3px solid rgba(99, 102, 241, 0.4);
  outline-offset: 2px;
}

button, [role="button"], a {
  cursor: pointer;
}
</style>
"""

import streamlit as st


def apply_global_styles() -> None:
    """Apply the shared DataMind visual system."""
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)
