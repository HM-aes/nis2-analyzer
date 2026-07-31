# Frontend Design Rules — HTML · HTMX · Alpine · CSS

These rules govern **all** frontend work in this repository. They are not
suggestions. If a request seems to require breaking one, stop and ask rather
than silently reaching for a different tool.

The stack is deliberately small. The goal is a server-rendered app where the
server owns the truth, HTMX moves HTML over the wire, Alpine handles local
interactivity, and CSS does the rest. No build step, no client-side framework,
no hydration.

---

## 0. Read this file on EVERY design task — not once per session

This is the first rule because it is the one that makes the others work.

**Before starting any frontend task — every template, partial, HTMX view,
Alpine component, or stylesheet — re-read this file from the top.** Do not rely
on having read it earlier in the session. Long sessions are where rules quietly
slip; the re-read is what prevents that.

**Open every frontend response with this compliance check, before any code:**

```
Design-rules check:
- Stack:              HTML/HTMX/Alpine/CSS only ✓
- Tokens:             styling via var(--…), no hardcoded hex ✓
- Server-owns-truth:  data from Django context / HTMX fragment ✓
- Motion:             CSS only, prefers-reduced-motion gated (or N/A) ✓
- Swap states:        loading + error present (or N/A) ✓
- Accessibility:      semantic HTML, focus states, contrast ✓
```

Any line that would be a ✗ means: **stop, fix it or ask, then proceed.** Code
produced without this check at the top of the response is incomplete — redo it
with the check.

This applies no matter how small the task. "Just tweak this button" still gets
the re-read and the check, because that is precisely the kind of task where a
stray inline hex or a non-semantic `<div onclick>` sneaks in.

---

## 1. The stack — and what is banned

**Use, in this order of preference:**
1. **Server-rendered HTML** (Django templates) — the default for everything.
2. **HTMX** — for anything that talks to the server after page load.
3. **Alpine.js** — for local interactivity that never needs the server.
4. **Plain CSS** — for all styling and motion.

**Do NOT introduce, suggest, or scaffold:**
- React, Vue, Svelte, Angular, Next, or any SPA framework — **even for a single component**, even "just for this widget."
- A JS build step: no Webpack, Vite, esbuild, Rollup, bundlers, or `npm run build` for frontend assets.
- JSX/TSX anywhere.
- Tailwind or any utility-class framework unless it is **already** configured in this repo — do not add it. Prefer semantic CSS with custom properties.
- CSS-in-JS, styled-components, Emotion.
- jQuery. Alpine covers what it did; HTMX covers the AJAX.
- Client-side routing. Django owns the URLs.
- Heavy animation libraries (Framer Motion, GSAP, anime.js) — CSS handles it. A
  small, framework-agnostic vanilla lib (e.g. Lenis for smooth scroll) is
  allowed **only** when explicitly requested and loaded via `<script>`.

If a task genuinely cannot be done in this stack, say so explicitly and explain
why before proposing anything outside it. Do not assume.

---

## 2. HTMX conventions

- **Every HTMX request hits a Django view that returns an HTML fragment**, not
  JSON. The server renders the partial; the client swaps it. Never return JSON
  to be assembled into DOM on the client — that is the SPA pattern this stack
  exists to avoid.
- **Partials live in `templates/**/partials/`** (or `_partials/`), named with a
  leading underscore: `_stat_row.html`, `_search_results.html`. A partial is a
  fragment with no `{% extends %}` — just the piece being swapped.
- **A view that serves both a full page and an HTMX swap** checks
  `request.htmx` (django-htmx) and renders the partial for HTMX requests, the
  full page otherwise. Prefer `django-htmx` for this; if it is not installed,
  check `request.headers.get("HX-Request")`.
- **Always include `{% csrf_token %}`** in any form, and rely on the
  `htmx.org` CSRF setup (the `hx-headers` on `<body>` or the
  `django_htmx` script) so non-form requests carry the token too. Never disable
  CSRF to make HTMX "work."
- **Prefer `hx-target` + `hx-swap` explicitly.** Don't rely on defaults for
  anything non-trivial; state the target and swap so the behaviour is readable.
- **Use `hx-trigger` intentionally.** `every Ns` polling and `hx-ext="sse"` are
  the right tools for live data (dashboards, queues, feeds) — reach for them
  before inventing a JS loop.
- **Loading and error states are required, not optional.** Every request that
  can be slow gets an `hx-indicator`; every request that can fail has a visible
  failure path. Do not ship a swap that silently does nothing on error.
- **Never put secrets, IDs a user shouldn't see, or trusted state in the DOM**
  as HTMX parameters. The server re-validates every request; the client is
  never trusted.

---

## 3. Alpine.js conventions

- **Alpine is for local, ephemeral UI state only** — toggles, tabs, dropdowns,
  a count-up animation, an open/closed menu, optimistic visual feedback. The
  moment state needs to persist or be authoritative, it belongs on the server
  via HTMX, not in Alpine.
- **Keep component logic small and inline for simple cases** (`x-data="{open:false}"`).
  For anything longer than a few lines, define a named factory
  (`x-data="dropdown()"`) in a `<script>` block, so the markup stays readable.
- **Do not rebuild server state in Alpine.** If you find yourself holding a list
  of records in Alpine and mutating them, stop — that is HTMX's job. Alpine
  should not be a client-side store.
- **Alpine and HTMX coexist; don't let them fight over the same DOM.** After an
  HTMX swap, Alpine re-initializes swapped-in nodes automatically (Alpine 3 +
  `htmx`), but never point both at mutating the same element's children. Let
  HTMX own swapped regions; let Alpine own purely-local widgets.
- **Prefer `x-show` for toggles, `x-if` only when the node must leave the DOM.**
- **Respect `x-cloak`** — add the `[x-cloak]{display:none}` rule so components
  don't flash unstyled before Alpine boots.

---

## 4. CSS conventions

- **Design tokens are mandatory and live in `:root` custom properties.** Colours,
  spacing, radii, fonts — all referenced as `var(--token)`. **Never hardcode a
  hex value inline** in a template or a second time in CSS; if a colour isn't a
  token yet, add the token. This is the rule that keeps the app off the
  "generic default" look and makes re-theming one file.
- **Colour should carry meaning where the app has status** (e.g. a "needs
  action" accent vs a "cleared" accent). Don't spend accent colour on
  decoration. Neutral by default; colour is a signal.
- **Motion is CSS-first:** transitions, `@keyframes`, `transform`/`opacity`
  (never animate layout properties like `width`/`top` when a `transform` will
  do). Trigger scroll animation with `IntersectionObserver` adding a class, not
  a library.
- **Always honour `prefers-reduced-motion: reduce`** — wrap non-essential motion
  so it's disabled for users who ask for that. This is an accessibility
  requirement, not a nicety.
- **Mobile-first, responsive by default.** Use `clamp()` for fluid type, CSS
  grid/flex for layout. Every layout must survive a 380px viewport.
- **No inline `style="..."` for anything reusable.** One-off structural nudges
  are tolerable; anything that repeats becomes a class.
- **Semantic HTML first:** real `<button>`, `<nav>`, `<header>`, `<section>`,
  landmark roles, alt text, focus-visible states, sufficient contrast. The dark
  theme is not an excuse for low-contrast muted text on muted background.

---

## 5. Templates & structure

- **`{% extends %}` + `{% block %}`** for full pages; **`{% include %}`** for
  reused chunks; **partials** for HTMX swaps. Know which of the three a given
  file is and name it accordingly.
- **One concern per template.** A page template composes includes and partials;
  it does not contain 400 lines of everything.
- **Keep logic out of templates.** Computation happens in the view or a helper;
  templates display. No heavy `{% with %}`/nested-`{% if %}` gymnastics that a
  view annotation would solve.
- **Assets are self-hosted in production.** CDN `<script>` tags for HTMX,
  Alpine, or fonts are fine for a prototype, but the production rule is: vendor
  them into `static/` and serve via whitenoise/your static pipeline. Never ship
  a customer-facing page depending on a third-party CDN being up.

---

## 6. When generating frontend code in this repo

1. **Default to the smallest tool that works:** static HTML > HTMX > Alpine. Don't
   add interactivity the request didn't ask for.
2. **Server owns truth.** Any real data, list, or state renders from Django
   context or arrives via an HTMX fragment — not hardcoded in JS, not held in
   Alpine.
3. **Tokens, not hex.** Style with `var(--token)`; add tokens when missing.
4. **Motion in CSS, gated on reduced-motion.**
5. **Every swap has a loading and an error state.**
6. **If the task pulls toward React/a build step/JSON-to-DOM, stop and flag it**
   instead of quietly switching stacks.

The test for any generated page: it should run by loading a Django template in a
browser with three `<script>` tags (htmx, alpine, optional lenis) and a
stylesheet — nothing compiled, nothing bundled.

---

## Reminder

Every frontend task begins by re-reading this file (§0) and opening with the
compliance check. If you have reached the end of a task and never produced that
check, the task was done wrong — go back and do it properly. The rules only hold
if they are revisited every time, not remembered vaguely from earlier.
