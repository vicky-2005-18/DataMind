# DataMind UI/UX Enhancement Plan

## Objective

Create a cohesive, accessible analytics workspace that helps users move confidently from project creation through dataset preparation, experimentation, comparison, prediction, and export.

## Design direction

- Professional analytics interface with restrained indigo and teal accents.
- Clear information hierarchy, compact dashboard density, and generous section spacing.
- Native Streamlit controls retained for reliability and accessibility.
- Semantic status colors with text labels; color never carries meaning alone.
- Minimal motion, visible keyboard focus, responsive layouts, and readable tables.

## Design system

### Color tokens

| Role | Value | Use |
|---|---:|---|
| Primary | `#4F46E5` | Primary actions, active navigation, focus |
| Primary hover | `#4338CA` | Hover and pressed states |
| Accent | `#0F766E` | Success-oriented analytics accents |
| Background | `#F6F7FB` | Application canvas |
| Surface | `#FFFFFF` | Cards, forms, data regions |
| Text | `#172033` | Primary text |
| Muted text | `#5F6B7A` | Captions and supporting text |
| Border | `#DDE2EA` | Dividers and card boundaries |
| Success | `#15803D` | Completed states |
| Warning | `#B45309` | Attention states |
| Error | `#B91C1C` | Validation and failures |

### Typography and spacing

- Use Streamlit's local sans-serif stack; do not depend on external font downloads.
- Maintain a consistent type scale and sequential heading hierarchy.
- Use an 8px spacing rhythm with 16px component and 24–32px section spacing.
- Keep long explanatory content within a readable measure.

## Implementation phases

### Phase 1 — Global foundation

- Add Streamlit theme configuration with accessible brand colors.
- Introduce centralized CSS tokens and shared surface, focus, button, form, table, and responsive rules.
- Standardize page headers with an eyebrow label, concise purpose, and visual divider.
- Redesign the sidebar brand, workspace context, grouped navigation, and runtime status.

### Phase 2 — Workflow clarity

- Show the product workflow as ordered stages: Workspace → Prepare → Model → Deliver → Learn.
- Improve empty states with a clear explanation and one next action.
- Replace implementation milestone language in user-facing navigation with task-oriented descriptions.
- Keep active project and dataset context visible without exposing internal IDs by default.

### Phase 3 — Home and onboarding

- Add a concise hero/value statement and a four-step getting-started path.
- Present project creation and existing projects as balanced workspace panels.
- Improve project state labels and selection affordances.
- Replace static activity copy with useful next-step guidance when no runs exist.

### Phase 4 — Data and experiment pages

- Group controls by intent and place advanced settings in expanders.
- Use explicit field help, units, validation feedback, and submission status.
- Place dataset/task scope next to every analytical result.
- Keep precise values available in tables alongside charts.

### Phase 5 — Visualization and comparison

- Prefer sorted bar charts for model/category comparisons.
- Add direct labels, meaningful titles, visible legends, and accessible table fallbacks.
- Use consistent metric formatting and status badges with text.
- Avoid radar charts when precise comparison matters.

### Phase 6 — Accessibility and responsive verification

- Verify visible keyboard focus and logical navigation order.
- Check text and component contrast against WCAG AA targets.
- Test at 375px, 768px, 1024px, 1366px, and 1440px widths.
- Verify long names, empty history, partial failures, and browser zoom.
- Respect reduced-motion preferences and avoid layout-shifting interactions.

## Acceptance criteria

- All pages share one visual system and page-header hierarchy.
- Navigation labels and grouping describe user tasks rather than milestones.
- Primary actions are visually consistent and keyboard focus is visible.
- Forms retain labels and produce explicit success or actionable error feedback.
- Charts include scope, labels, and a table or textual fallback where needed.
- Streamlit AppTest smoke tests and Ruff checks pass.
