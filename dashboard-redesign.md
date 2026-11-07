# Dashboard Redesign — "Obsidian" (shadcn × Aceternity, in-stack)

Reference document for the NIS2 Analyzer dashboard visual overhaul.
Written 2026-11-07. Keep this file updated as phases land — it is the
single source of truth for *why* the UI looks the way it does, so any
future session (or a different model) can continue without re-deriving
decisions.

> **Read `design-rules.md` first, every time.** Nothing in this document
> overrides it. All work is Django templates + HTMX + Alpine + plain CSS.

---

## 1. Hard constraints (what "use shadcn/Aceternity" means here)

- **shadcn/ui and Aceternity UI are React libraries. They are banned** by
  `design-rules.md` (no React, no build step, no JSX). We adopt their
  **visual language only** — colors, radii, border treatment, glow
  effects — re-implemented as plain CSS on design tokens.
- **Available frontend libraries** (verified: there is **no `package.json`**
  in this repo; nothing is npm-installed):
  - HTMX 1.9.12 (CDN, `base.html`)
  - Alpine.js 3.x + `$persist` plugin (CDN, `base.html`)
  - Tailwind **CDN build** (utility classes only; no config, no plugins —
    treat it as a spacing/layout shorthand, never for colors)
  - Fonts: Inter (UI), Fraunces (display), JetBrains Mono (data/mono)
  - Vendored in `frontend/static/js/`: `htmx.min.js`, `alpine.min.js`
    (self-hosting fallbacks)
- **Design-reference MCPs:** Mobbin MCP is connected but search requires a
  paid plan (checked 2026-11-07); there is no Awwwards MCP installed.
  Inspiration below is therefore from the shadcn "zinc" dark theme and
  Aceternity's published patterns (spotlight, grid backgrounds, gradient
  hairlines), not from fetched references. If Mobbin becomes available,
  good queries: "security analytics dashboard dark mode", "compliance
  dashboard stat cards".

## 2. CSS architecture (load order matters — keep it)

`frontend/templates/dashboard/base.html` loads, in order:

1. `static/css/tokens.css` — **all design tokens.** The only place colors
   are defined. Hex is allowed **only** in the `@supports not (oklch)`
   fallback block.
2. `static/dashboard/css/sidebar.css` — sidebar (own bridged vars in
   `dashboard-theme.css`; deliberately untouched by this redesign).
3. `static/dashboard/css/dashboard.css` — component library (cards,
   tables, forms, pills, badges…).
4. `static/css/dashboard.css` — older/second component file (filter bar,
   scards). Candidate for merge, see §6 Phase 4.
5. `static/dashboard/css/dashboard-theme.css` — dark-mode alias bridge
   (`.main-content` token aliases, sidebar var bridge).
6. `static/dashboard/css/dashboard-polish.css` — **top polish layer**
   (atmosphere, card elevation, KPI identity, dropdown listbox). Loaded
   last; most redesign work lands here or in `tokens.css`.
7. `static/dashboard/js/select-dropdown.js` — progressive enhancement
   that turns every `<select>` into the themed `.dd` listbox.

When editing any of these, **bump the `?v=` query** on its `<link>` in
`base.html` or the browser serves the stale file.

## 3. Audit findings (2026-11-07, pre-redesign)

Screenshots: dashboard home, clients, gaps pages at 1440×900, dark.

**Theme**
- F1. Canvas is *slate* (`--background: oklch(0.165 0.007 265)` ≈ `#12151b`,
  visibly blue-grey), not the near-black neutral of shadcn dark /
  Aceternity. Cards at `0.205` sit close to the canvas, so elevation
  reads muddy rather than layered.
- F2. Borders (`0.335`) are brighter than shadcn's hairline look; cards
  feel "outlined" instead of "lit from above".
- F3. Two radial accent glows (amber + blue) in `.page-content::before`
  are a good Aceternity instinct but fight the slate canvas; on
  near-black they will read far better.

**Cards**
- F4. KPI cards use **inline hex** left-borders in templates
  (`style="border-left-color:#EF4444"` in `gaps.html`, `audits.html` …) —
  violates the tokens rule and paints 4 loud color bars in a row.
  shadcn stat cards are neutral with one small colored signal (delta
  badge / icon), color = meaning only.
- F5. Card headers were already flattened to hairlines by the polish
  layer (good); but cards lack the signature "top edge light" — a 1px
  gradient highlight on the upper border that sells the dark-glass look.
- F6. Hover lifts cards by `-3px` with a big shadow; slightly toy-like at
  this scale. Calmer: 1–2px rise, shadow deepens, border brightens.

**Other (not blocking, queued in Phase 4+)**
- F7. Two parallel `dashboard.css` files define overlapping components.
- F8. Emoji used as icons (🛡️ 🔍 📊) — fine for now, inconsistent
  weights; a single-color SVG set would look more professional.
- F9. `audit_detail.html` carries 16 pre-existing design-hook findings
  (low-contrast white-on-red badges, cramped padding) — blocked edits
  there earlier; needs its own cleanup pass before restyling.
- F10. Treemap cell colors are computed with inline `rgba(37,99,235,…)`
  in `gaps.html` — hex/inline color again.

## 4. Direction — "Obsidian"

One sentence: **near-black neutral canvas, cards as faintly-lit glass
panels with hairline borders and a top-edge light, color appearing only
as meaning (status, one brand accent), one soft ambient glow.**

Principles (checkable):
1. Canvas ≈ `oklch(0.145)` neutral (shadcn zinc-950 territory), hue
   drained to near-zero chroma. The app should read *black* at a glance.
2. Exactly three elevation steps: canvas → card (+0.04 L) → inset/hover
   (+0.04 L). Nothing else.
3. Borders are hairlines ~`oklch(0.28)`; emphasis comes from the top-edge
   light and shadow, not brighter outlines.
4. Brand amber stays the **only** decorative accent (focus rings, active
   nav, CTA, ambient glow). Red/green/yellow appear **only** on status.
5. Motion: ≤200ms, opacity/transform only, gated on
   `prefers-reduced-motion`.
6. Text contrast ≥ 4.5:1 for body text on every surface it sits on.

## 5. Token map (tokens.css) — old → new

Hue moves 265 → 285 (blue-slate → neutral zinc), chroma ≈ halved.

| Token | Old (oklch) | New (oklch) | Hex fallback |
|---|---|---|---|
| `--background` | 0.165 0.007 265 | **0.145 0.004 285** | `#0c0c0e` |
| `--surface` | 0.205 0.008 265 | **0.185 0.005 285** | `#151518` |
| `--surface-secondary` | 0.245 0.009 265 | **0.225 0.006 285** | `#1d1d21` |
| `--border` | 0.335 0.010 265 | **0.295 0.007 285** | `#333338` |
| `--border-strong` | 0.435 0.012 265 | **0.415 0.009 285** | `#55555c` |
| `--separator` | 0.275 0.008 265 | **0.245 0.006 285** | `#222226` |
| `--header-strip` | 0.270 0.009 265 | **0.240 0.006 285** | `#212125` |
| `--foreground` | 0.955 0.004 265 | 0.960 0.002 285 | `#f2f2f4` |
| `--muted` | 0.720 0.010 265 | 0.730 0.006 285 | `#a6a6af` |
| `--dim` | 0.575 0.010 265 | 0.590 0.008 285 | `#7d7d86` |
| `--filter-bg` | 0.275 0.009 265 | 0.235 0.006 285 | `#202024` |
| `--filter-bg-hover` | 0.315 0.010 265 | 0.275 0.007 285 | `#2a2a2f` |
| accent / status | unchanged | unchanged | — |

Derived tokens (`color-mix` on the above) update automatically. The
sidebar keeps its own bridged values in `dashboard-theme.css` — decide
separately whether to deepen it to match (Phase 3).

## 6. Plan

- **Phase 1 — Theme tokens** ✅ *(this session)*
  `tokens.css`: apply §5 table to both the oklch block and the hex
  fallback block. Bump `tokens.css?v=`. No template changes.
- **Phase 2 — Card system** ✅ *(this session)*
  `dashboard-polish.css`:
  - Add top-edge light: 1px gradient line via `::after` on
    `.card/.scard/.kpi-card` (white 10% → transparent), reduced-motion
    safe (static).
  - Calm hover: `translateY(-1px)`, border → `--border-strong`, deeper
    shadow; remove the `-3px` jump.
  - Deepen `--pl-sheen` to start from `white 5%` so cards read as lit
    glass on the darker canvas.
  - KPI cards: neutralize the colored left-border look at the polish
    layer (left border → hairline; color moves to the small icon chip +
    value delta only). Inline hex in templates still *present* but
    visually overridden; actual template cleanup is Phase 4.
- **Phase 3 — Sidebar + topbar match** ☐
  Deepen sidebar bridge vars in `dashboard-theme.css` to the new scale
  (card `0.165`, borders `0.26`); verify active/hover states; keep the
  amber active accent.
- **Phase 4 — Template hygiene** ☐
  Replace every inline `style="border-left-color:#…"` and
  `rgba(37,99,235,…)` with token classes (`.kpi--danger`,
  `.treemap-cell` opacity steps); merge the two `dashboard.css` files;
  fix `audit_detail.html`'s 16 pre-existing findings (F9).
- **Phase 5 — Wow layer (optional, each gated on reduced-motion)** ☐
  - Aceternity-style dotted-grid canvas texture (CSS radial-gradient
    dots, masked to fade at edges).
  - Count-up on KPI values (Alpine, local state only).
  - Score ring charts with `conic-gradient` on audit cards.
  - Hover spotlight on cards (CSS `radial-gradient` at
    `var(--mx) var(--my)` set by a 3-line pointermove listener — decide
    whether that JS is acceptable before building).

## 7. Verification checklist (run after every phase)

- Pages: `/dashboard/`, `/dashboard/clients/` (+ `/new/`),
  `/dashboard/audits/`, `/dashboard/gaps/`, `/dashboard/audits/<id>/`
  at 1440px and 380px.
- Dropdowns (`.dd`) open above content, menu surface uses `--filter-bg`.
- Body text ≥ 4.5:1 on `--surface` and `--surface-secondary`.
- `prefers-reduced-motion: reduce` kills lifts/pops but UI stays usable.
- Sidebar unaffected (until Phase 3).
- `?v=` bumped for every edited static file.

## 8. Decision log

- 2026-11-07 Direction named "Obsidian"; hue 285/low-chroma chosen over
  pure 0-chroma black to keep a hint of warmth under the amber accent.
- 2026-11-07 Mobbin unavailable (paid plan); proceeded on shadcn zinc +
  Aceternity conventions from knowledge. No Awwwards MCP exists in this
  workspace.
- 2026-11-07 KPI color bars demoted to icon-chip color only (F4):
  four simultaneous color bars diluted status meaning (§4 principle 4).
