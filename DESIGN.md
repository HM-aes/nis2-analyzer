# Design

Extracted from the existing code (`frontend/static/css/tokens.css`, `frontend/static/marketing/css/base.css`, dashboard stylesheets). Run `/impeccable document` for a full pass.

## Visual Theme
Dark only (`color-scheme: dark`). Cool slate surfaces in the content area, a near-black zinc shell around it (sidebar, page frame). Restrained color: neutrals carry the surface, one orange accent used sparingly, status colors for audit and gap state.

## Color (dashboard, `tokens.css`)
- Background `--bg` #0e1116; surface `--surface` #151922; hover `--surface-hover` #1a2029
- Shell `--shell-bg` oklch(0.141 0.005 285.8), `--shell-card`, `--shell-raised`
- Text `--text` #e8eaed; muted `--text-muted` #9aa3b2; dim `--dim` #8a93a0
- Borders: white at 7% (`--border`), 14% (`--border-strong`)
- Accent (shield orange) `--accent` oklch(0.705 0.155 55), with `--accent-soft` / `--accent-border` mixes. Use sparingly.
- Status: `--success` oklch(0.72 0.15 155), `--warning` oklch(0.80 0.14 75), `--danger` oklch(0.68 0.19 27), each with `-soft`, `-text`, `-edge` variants
- Data: `--stat-blue` oklch(0.70 0.12 245)
- Always style through `var(--…)`; hex only in the `@supports not (oklch)` fallback.

## Color (landing, `marketing/css/base.css`)
Separate token set: `--bg` #0B0E13, `--panel` #131820, `--ink` #EAEEF4, `--amber` #E0A82E (action / deadline / risk), `--green` #3FB68B (compliant).

## Typography
- Fraunces (serif, weights 400–560): page titles and display headings, letter-spacing about -0.02em
- Inter (400–700): all UI and body text
- JetBrains Mono (500–600): numbers, IDs, article references, metadata

## Shape and Depth
- Radii: `--radius` 10px, `--radius-sm` 8px, `--radius-badge` 6px; pills fully rounded
- Cards: subtle inset highlight (`--card-inset`), `--shadow-sm` / `--shadow-md`
- Card headers use an elevated strip (`--card-header-*` tokens)

## Stack constraints
Django templates + HTMX + Alpine.js + plain CSS. No build step, no SPA frameworks. See `design-rules.md`.
