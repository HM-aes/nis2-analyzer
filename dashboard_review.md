# Dashboard Review — NIS2 Compliance Analyzer

**Date:** 2026-05-14  
**Reviewer:** Claude Code (Sonnet 4.6)  
**Scope:** All template HTML, views, Alpine.js interactions, URL routing, static files

---

## 1. What's Currently Built and Working

### Authentication & Navigation
- Full login/logout flow with username/password (`DashboardLoginView`, `DashboardLogoutView`)
- Public landing page (`home.html`) with animated hero, RAG pipeline visualization, sample compliance gauge
- Sidebar navigation with active-link detection via `{% if 'client' in request.resolver_match.url_name %}`
- Avatar dropdown with `@click.away` close behavior (Alpine.js)
- Dark/light theme toggle with `localStorage` persistence (`nis2-theme`)
- HTMX CSRF token injection via `htmx:configRequest` event listener
- `LoginRequiredMixin` on all authenticated views; superuser vs. account-manager permission splits

### Dashboard Home (`dashboard.html`)
- 4 KPI cards: Total Clients, Active Audits, Avg Compliance Score, Open Critical Gaps
- Kanban pipeline board with 6 status columns (INTAKE → DELIVERED), overflow counters, mini audit cards
- Compliance score distribution histogram (5 buckets, gradient fills)
- Gaps-per-category stacked bar chart (8 categories, 4 severity colors)
- Recent activity feed (10 audits + 10 critical/high gaps with relative timestamps)
- Admin-only revenue summary (quoted/paid/unpaid, EUR formatted)

### Clients (`clients.html`, `client_rows.html`)
- Client table with HTMX live search (`hx-trigger="keyup changed delay:300ms"`)
- Sector and size filter dropdowns that send with HTMX include
- Row click navigation (`onclick="window.location=..."`)
- Score bars color-coded by performance threshold (red/yellow/green)
- Empty state with "Eerste klant toevoegen" CTA

### Client Detail (`client_detail.html`)
- Two-column layout (70/30): main info + sidebar cards
- Alpine.js edit toggle (`x-data="{ editing: false }"`) — display/edit mode switch
- Audit history table with score bars, duration, paid status, view/download buttons
- Compliance trend mini bar chart (requires ≥2 completed audits)
- Sector benchmark card showing average compliance for same sector
- Quick action buttons: new audit, download latest report

### New Client Form (`client_new.html`)
- Three-section form: company info, contact info, address
- Real-time KVK validation with Alpine.js regex (`/^\d{8}$/`) and `:class` conditional border
- Server-side validation with `form-error` display
- Sector select and company size radio buttons

### Audits (`audits.html`, `audit_rows.html`)
- Status and tier filter pills with HTMX partial swap (`hx-target="#audit-tbody"`)
- Active pill highlighted via Django template conditional
- Table columns: client, tier, status (spinner if PROCESSING), score bar, gaps, docs, created, duration, paid, view

### Audit Detail (`audit_detail.html`)
- Large compliance gauge (SVG circle with `stroke-dasharray`, color-coded by score)
- Status/tier/size badges, timestamp metadata
- HTMX polling block: `hx-trigger="every 3s"` during PROCESSING/ANALYSIS
- Alpine.js tab navigation with `x-transition` (4 tabs: Overview, Gap Analyse, Documenten, Timeline)
- Tab 1 (Overview): severity breakdown boxes, category heatmap (8 cells, opacity by gap count), remediation summary (hours + cost)
- "AI Analyse Starten" button (gated on INTAKE status + docs present)
- "Rapport Downloaden" button (gated on `report_generated`)

### Audit Status Partial (`audit_status.html`)
- 5-step progress visualization (Documents → Knowledge Retrieval → Claude → Scoring → Report)
- ✅/🔄/○ indicators per step based on current status
- Success/review/error states (green 🎉, orange ⚠️)

### Gap Analysis (`gaps.html`)
- KPI bar: Total Gaps, Critical & Open, Avg Risk Score, Total Remediation Hours
- Category treemap with `{% widthratio %}` for flex-basis widths and opacity-based risk coloring
- HTMX treemap click → filter table by category
- Alpine.js filter state (`severity`, `category`, `addressed`) with real-time row show/hide
- Expandable gap rows with `x-data="{ expanded: false }"` and 2-column current/required state layout

### Document Upload
- `UploadDocumentView` accepts PDF/DOCX/TXT, creates `ClientDocument`, spawns background thread for docling text extraction
- Audit document count updated on upload
- Background pipeline worker: docling extraction → Qdrant search (5 query types, top_k=5, dedup top 25) → NIS2Auditor → gap records → audit score/status update

### URL Routing (15 routes)
All routes functional — authentication, CRUD pages, HTMX partials, upload, run pipeline.

---

## 2. What's Incomplete or Missing

### Templates with Placeholder/Stub Content

| Template | Missing |
|---|---|
| `audit_detail.html` — Tab 2 | Gap Analysis tab: filter bar and gap table exist but inline expand form, mark-as-addressed action, and notes field are not confirmed wired |
| `audit_detail.html` — Tab 3 | Documents tab: no confirmed file listing, delete, re-process, or document-type display |
| `audit_detail.html` — Tab 4 | Timeline tab: referenced in PRD and tab nav, but no confirmed template content |
| `client_detail.html` | Edit client form: Alpine.js toggle `x-show="!editing"` switches display but the actual editable form HTML is unconfirmed — no POST route for client update |
| `gap_rows.html` | Referenced by `HtmxGapRows` view and gaps.html treemap click, but not confirmed to exist or be complete |

### Missing Views / Endpoints

| Function | Status |
|---|---|
| `PATCH /clients/<pk>/` or POST edit form | No URL or view for client update |
| `POST /audits/<pk>/mark_complete/` | No way to move REVIEW → COMPLETE from UI |
| `POST /audits/<pk>/mark_delivered/` | No way to mark COMPLETE → DELIVERED from UI |
| `POST /gaps/<pk>/address/` | No way to mark a gap as addressed from UI |
| `POST /audits/<pk>/generate_report/` | PDF generation logic not exposed via dashboard (only REST API) |
| Audit creation (`/audits/new/`) | No URL or view — audits can only be created via REST API |
| User management / invite consultant | No UI for admin to create users or assign account managers |
| Password reset / change password | No UI |

### Business Logic Gaps

- **Audit creation from dashboard:** Users cannot create a new audit from the dashboard UI — there is a "+ Nieuwe Audit Starten" quick-action button on client detail that links nowhere functional (no `dashboard:audit_new` route exists).
- **Status transition controls:** The pipeline can be triggered (INTAKE → PROCESSING) but there is no UI to advance REVIEW → COMPLETE → DELIVERED, nor to reject/reset a failed analysis.
- **Gap addressed workflow:** Gaps have `addressed`, `addressed_date`, `implementation_notes` fields, but there is no dashboard action to set them.
- **Report generation:** `report_generated` flag gates the download button, but the PDF generation step is not called anywhere in the dashboard pipeline — audits complete but `report_generated` stays `False`.
- **Document type selection:** Upload form does not expose `document_type` field — all uploads default to unknown type.
- **Knowledge base management:** `KnowledgeDocument` model and Qdrant ingestion exist but there is no admin or dashboard page to add/manage NIS2 knowledge documents.

### Data Not Yet Surfaced

- `business_impact` field on ComplianceGap — never shown
- `implementation_notes` and `addressed_date` on ComplianceGap — never shown
- `internal_notes` and `client_feedback` on ComplianceAudit — never shown
- `key_topics`, `relevance_score`, `language_detected` on ClientDocument — never shown
- `virus_scanned`, `pii_detected` flags on ClientDocument — never shown in UI

---

## 3. UI/UX Gaps for a SaaS NIS2 Product

### Navigation & Information Architecture

**Problem:** The sidebar has only 4 items (Dashboard, Klanten, Audits, Gap Analyse) with no hierarchy. As data grows, users will need sub-navigation or breadcrumbs to orient themselves.

**Problem:** No breadcrumb trail. On `audit_detail.html`, the only "back" affordance is a `← {{ client.company_name }}` button — no full path (Dashboard > Clients > ACME > Audit #42).

**Problem:** No page titles in the browser `<title>` tag (likely defaults to the base template value) — bad for bookmarking and multi-tab workflows.

### Empty States

The dashboard KPI cards show raw numbers (e.g., "0 clients") but give no call-to-action when there is no data. A new user logging in for the first time sees a blank kanban board with no "Get started" prompt.

### Audit Creation Flow

There is a critical flow break: the "+ Nieuwe Audit Starten" button on `client_detail.html` has no target route. This is the primary action consultants will use daily. Without it, audits can only be created via the `/api/audits/` REST endpoint.

### Gap Addressed Workflow

Gaps are the core deliverable. Consultants need to:
1. Mark a gap as addressed after client remediation
2. Add implementation notes
3. Track addressed date

None of this is available in the UI. The `gaps.html` Alpine.js filter has an `addressed` pill but clicking it is decorative — there is no way to actually mark gaps addressed.

### Audit Status Transitions

Audits that reach REVIEW status (AI flagged them for manual review, or processing completed) are stuck there. A consultant needs a "Mark as Complete" button visible on `audit_detail.html` when status is REVIEW.

### Report Generation UX

The "Rapport Downloaden" button is conditionally hidden if `report_generated = False`. After an audit completes, `report_generated` is never set to `True` by the dashboard pipeline — so the button is always hidden. Users have no feedback that the report doesn't exist yet or how to generate it.

### Form Feedback

- `client_new.html` shows field-level errors but the form does not scroll to the first error on submit — users may not notice validation failures if the error is below the fold.
- No success toast or confirmation after saving a new client (redirects silently to client list).
- No loading state on the "AI Analyse Starten" button — users may click multiple times.

### Compliance Score Presentation

- The compliance score gauge on `audit_detail.html` shows a raw percentage but no context ("Is 67% good for my sector?"). The sector benchmark is shown on `client_detail.html` but not carried into the audit detail view.
- No NIS2 article explorer or explanation of what each gap article means — consultants need this when presenting findings.

### Mobile / Responsive

- The sidebar is always visible with no collapse mechanism confirmed in the templates. On a 13" laptop, the content area is narrow.
- The kanban board (`dashboard.html`) is a 6-column grid — it will overflow horizontally on small screens.
- The audit detail tab panels have dense tables that do not have a confirmed horizontal scroll wrapper for narrow viewports.

### Accessibility

- The kanban audit mini-cards and treemap cells use `cursor-pointer` but are `<div>` elements with `onclick` rather than semantic `<button>` or `<a>` — keyboard-inaccessible.
- The SVG gauge has no `aria-label` or `role` attribute — screen readers cannot convey the score.
- Color is used as the sole indicator of severity in the heatmap and score bars — no text or icon fallback for color-blind users.

### Missing SaaS Utility Pages

- No profile/settings page for the logged-in consultant
- No notification center (bell icon in topbar links to nothing)
- No help/documentation link
- No "what's new" or changelog
- No onboarding checklist for new tenants

---

## 4. Specific Recommendations to Improve

### Priority 1 — Fix Broken Core Flows

**A. Audit creation view**

Add `dashboard:audit_new` route and `NewAuditView`. The form should require selecting a client, tier, and quoted price. Redirect to `audit_detail` on success.

```python
# dashboard/views.py
class NewAuditView(LoginRequiredMixin, View):
    def get(self, request):
        clients = Client.objects.filter(...).order_by('company_name')
        return render(request, 'dashboard/audit_new.html', {'clients': clients, 'tier_choices': ComplianceAudit.TIER_CHOICES})

    def post(self, request):
        audit = ComplianceAudit.objects.create(
            client_id=request.POST['client'],
            tier=request.POST['tier'],
            quoted_price=request.POST['quoted_price'],
            status='INTAKE',
        )
        return redirect('dashboard:audit_detail', pk=audit.pk)
```

**B. Client update view**

Add `PATCH /dashboard/clients/<pk>/edit/` and wire the Alpine.js edit toggle form to POST to it. The current `x-data="{ editing: false }"` toggles display but there is no `<form>` with `action` attribute in edit mode.

**C. Report generation**

Call `generate_report()` (or create one) inside `_run_nis2_pipeline()` after gaps are saved, and set `report_generated = True`. The download button will then appear automatically. Until PDF generation is implemented, generate a JSON or HTML report as a placeholder.

```python
# In _run_nis2_pipeline, after saving gaps:
audit.report_generated = True
audit.report_generated_at = timezone.now()
audit.save(update_fields=['report_generated', 'report_generated_at'])
```

### Priority 2 — Gap Workflow

**A. Mark gap as addressed**

Add `POST /dashboard/gaps/<pk>/address/` HTMX endpoint that sets `addressed=True`, `addressed_date=today`. Return the updated row partial.

```html
<!-- In gap row -->
<form hx-post="{% url 'dashboard:gap_address' gap.pk %}" hx-target="closest tr" hx-swap="outerHTML">
  {% csrf_token %}
  <button type="submit" class="btn btn-ghost btn-sm">Mark Addressed</button>
</form>
```

**B. Audit status transitions**

Add action buttons on `audit_detail.html` for consultants:
- REVIEW → COMPLETE: "Analyse Goedkeuren" button
- COMPLETE → DELIVERED: "Rapport Geleverd" button
- Any state → INTAKE: "Opnieuw Starten" button (for failed analyses)

Wire each to a `POST /dashboard/audits/<pk>/transition/` view with `?to=COMPLETE` parameter.

### Priority 3 — Audit Detail Tabs

**A. Documents tab (Tab 3)**

Build `partials/document_list.html` showing:
- Filename, type badge, size, upload date, processed status
- Security flags: virus scan result, PII detected (color-coded)
- Delete button per document

**B. Timeline tab (Tab 4)**

Show chronological audit events:
- Created, started, completed, delivered timestamps
- Each gap created with its severity
- Document uploads with filenames
- Status transitions

This can be assembled from existing model timestamps without a separate event log model.

**C. Gap Analysis tab (Tab 2) — mark addressed inline**

Each gap row expanded view should include the mark-addressed form inline, plus an `implementation_notes` textarea that PATCHes via HTMX.

### Priority 4 — Dashboard UX Polish

**A. Add breadcrumbs**

Add a `{% block breadcrumb %}` in `base.html` rendered below the topbar. Each page defines its path. This is purely template work.

```html
<!-- base.html -->
<nav class="breadcrumb" aria-label="Breadcrumb">
  {% block breadcrumb %}{% endblock %}
</nav>
```

**B. Loading state on "AI Analyse Starten"**

Disable the button and show spinner on click:

```html
<button
  hx-post="{% url 'dashboard:audit_run' audit.pk %}"
  hx-indicator="#run-spinner"
  x-data="{ running: false }"
  @click="running = true"
  :disabled="running"
>
  <span x-show="running" class="spinner"></span>
  AI Analyse Starten
</button>
```

**C. Success/error toast notifications**

Add a `messages` block in `base.html` that renders Django messages as auto-dismissing toasts using Alpine.js `x-show` with a timeout.

**D. Empty state CTAs on dashboard**

When `total_clients == 0`, replace the kanban board with an onboarding card:
```
"Welkom bij NIS2 Analyzer — voeg uw eerste klant toe om te beginnen."
[+ Klant Toevoegen]
```

**E. Notification bell**

Either wire the topbar bell to a real notifications endpoint, or remove it to avoid dead UI elements.

### Priority 5 — Data Surfacing

**A. Business impact on gaps**

Add `business_impact` as a third panel in the expanded gap row (next to Current State / Required State).

**B. Document security flags on document tab**

Show `virus_scanned`, `pii_detected`, `language_detected` as small badges on each document row — this is a key trust signal for a security SaaS product.

**C. Sector benchmark on audit detail**

The `client_detail.html` sidebar shows sector average. Carry this into `audit_detail.html` context so the gauge label reads "67% (sector avg: 72%)".

---

## 5. What Needs Building Next

Ordered by business value and dependency.

### Sprint 1 — Core Feature Completeness (1–2 weeks)

1. **Audit creation form** (`audit_new.html` + `NewAuditView`) — blocks all new audit workflows from UI
2. **Client edit form** — the Alpine.js toggle exists but the form and route do not
3. **Audit status transition actions** — REVIEW → COMPLETE → DELIVERED buttons with confirmation modal
4. **Report generation hook** — set `report_generated=True` in pipeline so download button appears
5. **Gap mark-as-addressed** — HTMX POST endpoint + inline form in gap rows

### Sprint 2 — Audit Detail Completion (1 week)

6. **Documents tab** (`partials/document_list.html`) with security flag display
7. **Timeline tab** assembled from existing timestamps
8. **Gap Analysis tab** inline mark-addressed + implementation notes
9. **`gap_rows.html` partial** — verify it exists and is complete; add if missing

### Sprint 3 — UX & Polish (1 week)

10. **Breadcrumb navigation** in base template
11. **Django messages as toasts** — success/error feedback on all POST actions
12. **Empty state CTAs** — zero-data states on dashboard, clients, audits
13. **Loading states** on all async-trigger buttons (run audit, upload document)
14. **Page `<title>` tags** — per-page titles in base template `{% block title %}`
15. **Remove dead topbar links** — notification bell and any stub SSO buttons

### Sprint 4 — Knowledge Base & Admin Tools (1–2 weeks)

16. **Knowledge document ingestion UI** — upload + ingest NIS2 documents into Qdrant from dashboard
17. **User management page** — admin creates consultant accounts, assigns to clients
18. **Audit notes panel** — `internal_notes` and `client_feedback` fields editable by consultants

### Sprint 5 — Analytics & Reporting (2 weeks)

19. **PDF report generation** (ReportLab) — executive summary, gap table, remediation roadmap
20. **Trend charts** — compliance score over time per client, per sector aggregate
21. **Export to CSV/Excel** — gap table export for consultants
22. **Sector comparison dashboard** — cross-client benchmark visualization

### Sprint 6 — Client Portal (3+ weeks)

23. **Separate client-facing login** — read-only view of their audit results
24. **Public report URL** — shareable, token-authenticated report page
25. **Stripe integration** — invoice generation and payment flow tied to audit tier

---

## Summary

The dashboard is approximately **70–75% complete** as a functional internal tool. The design system, data model, AI pipeline, and most read-only views are solid. The primary gaps are:

- **Two critical broken flows:** audit creation and client editing have no backend route
- **Three missing action verbs:** mark gap addressed, transition audit status, generate report
- **One incomplete section:** audit detail tabs 2–4 are partially or fully unbuilt
- **Zero onboarding affordances:** a new user sees a blank dashboard with no guidance

Fixing Sprint 1 items makes the product usable for real consulting work. Everything after that improves quality and prepares for client-facing or commercial features.
