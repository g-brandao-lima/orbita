# Phase 5: Web Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 05-web-dashboard
**Areas discussed:** Layout structure, Price chart library, Form handling, Signal indicators
**Mode:** Auto (all decisions auto-selected with recommended defaults)

---

## Layout structure

| Option | Description | Selected |
|--------|-------------|----------|
| Multi-page with navigation | Each page has clear purpose, simpler with Jinja2 | Yes |
| Single page with tabs | All content on one page, more dynamic | |
| Sidebar navigation | Left sidebar with group list | |

**User's choice:** [auto] Multi-page with navigation (recommended default)
**Notes:** Aligns with no-JS-framework constraint. Jinja2 renders each page server-side.

---

## Price chart library

| Option | Description | Selected |
|--------|-------------|----------|
| Chart.js via CDN | Widely used, no build step, good line charts | Yes |
| Lightweight alternative (uPlot) | Smaller, faster, less features | |
| ASCII/table-based | No JS at all, just numbers | |

**User's choice:** [auto] Chart.js via CDN (recommended default)
**Notes:** Only JS dependency, loaded via CDN. No build step needed.

---

## Form handling

| Option | Description | Selected |
|--------|-------------|----------|
| Standard HTML forms with POST | Simplest, no JS, server-side processing | Yes |
| HTMX for partial updates | More dynamic, still mostly server-side | |
| Fetch API to existing JSON endpoints | Reuses API directly, needs JS | |

**User's choice:** [auto] Standard HTML forms with POST (recommended default)
**Notes:** Aligns with no-JS-framework constraint from PROJECT.md.

---

## Signal indicators

| Option | Description | Selected |
|--------|-------------|----------|
| Color-coded badges | Gray/yellow/orange/red, universally understood | Yes |
| Icon-based | Different icons per urgency level | |
| Text labels | Written urgency level (MEDIA, ALTA, MAXIMA) | |

**User's choice:** [auto] Color-coded badges (recommended default)
**Notes:** Simple visual hierarchy. Combined with text for accessibility.

---

## Claude's Discretion

- Template structure (base.html + page templates)
- Visual styling (colors, spacing, fonts)
- Feedback messages after form actions
- Responsive layout implementation

## Deferred Ideas

None.
