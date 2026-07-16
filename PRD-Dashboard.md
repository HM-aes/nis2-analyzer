# PRD — NIS2 Compliance Analyzer Dashboard
**Version:** 1.0
**Date:** 2026-02-23
**Author:** Product Team
**Status:** Ready for Development

---

## 1. Executive Summary

The NIS2 Compliance Analyzer backend is fully operational — it ingests client documents, runs AI-powered gap analysis via Claude Sonnet, and stores structured compliance results in PostgreSQL. What is missing is a **professional web dashboard** that allows consultants to manage clients, trigger audits, monitor AI processing in real time, and deliver polished reports to Dutch IT companies.

This PRD defines the complete dashboard product: every screen, every data point, and every interaction — using the existing REST API as the sole data source.

---

## 2. Target Users

| User | Description | Primary Need |
|------|-------------|--------------|
| **Compliance Consultant** | Main daily user. Creates clients, uploads docs, triggers analysis, delivers reports. | Fast audit workflow, clear gap overview |
| **Account Manager** | Owns client relationships. Sees only their own clients. | Client health at a glance, revenue tracking |
| **Admin / Superuser** | Full platform oversight. | All clients/audits, system health, financials |

---

## 3. Design Principles

1. **Professional & trustworthy** — This is a compliance product used by serious Dutch enterprises. Clean, corporate aesthetic. Dark sidebar, light content area.
2. **Data-dense but not cluttered** — Show the right KPIs without overwhelming. Use progressive disclosure.
3. **Status-first** — Every list view shows audit status prominently. Color-coded badges make pipeline state scannable.
4. **Dutch context** — Currency in € (euro), dates in DD-MM-YYYY, locale `nl-NL`. KVK numbers displayed with formatting.
5. **Action-oriented** — Every screen has a clear primary action. No dead ends.

---

## 4. Color System & Visual Language

### Status Colors (used across the entire app)

| Status | Color | Hex | Usage |
|--------|-------|-----|-------|
| INTAKE | Slate | `#64748B` | Waiting for documents |
| PROCESSING | Amber | `#F59E0B` | AI running (pulse animation) |
| ANALYSIS | Blue | `#3B82F6` | Claude analyzing |
| REVIEW | Orange | `#F97316` | Needs human attention |
| COMPLETE | Green | `#22C55E` | Finished successfully |
| DELIVERED | Emerald | `#10B981` | Delivered to client |

### Severity Colors (gaps)

| Severity | Color | Hex |
|----------|-------|-----|
| CRITICAL | Red | `#EF4444` |
| HIGH | Orange | `#F97316` |
| MEDIUM | Yellow | `#EAB308` |
| LOW | Slate | `#64748B` |

### Base Palette

- **Background:** `#F8FAFC` (near-white)
- **Sidebar:** `#0F172A` (near-black navy)
- **Sidebar accent:** `#1E40AF` (deep blue)
- **Card surface:** `#FFFFFF`
- **Border:** `#E2E8F0`
- **Primary action:** `#2563EB` (blue-600)
- **Text primary:** `#0F172A`
- **Text muted:** `#64748B`

### Typography

- **Font:** Inter (Google Fonts) — clean, professional, reads well in Dutch
- **Headings:** 600 weight
- **Body:** 400 weight
- **Monospace (UUIDs, KVK):** JetBrains Mono

---

## 5. Navigation Structure

```
Sidebar (always visible, collapsible on mobile)
│
├── 🏠  Dashboard          → /dashboard
├── 👥  Clients            → /clients
│   ├── New Client         → /clients/new
│   └── [Client Detail]    → /clients/:id
│
├── 📋  Audits             → /audits
│   ├── New Audit          → /audits/new
│   └── [Audit Detail]     → /audits/:id
│
├── 🔍  Gap Analysis       → /gaps  (global gap browser)
│
├── 📄  Documents          → /documents
│
└── ⚙️  Settings           → /settings  (future)

Header (top bar)
├── Search (clients, audits by name/KVK)
├── Notifications bell (REVIEW status alerts)
└── User avatar + logout
```

---

## 6. Screens

---

### 6.1 Dashboard (Home)

**Route:** `/dashboard`
**Purpose:** Single-screen overview of the entire business operation.

#### 6.1.1 KPI Cards (top row — 4 cards)

| Card | Value | Sub-label | Source |
|------|-------|-----------|--------|
| Total Clients | Count of all clients | `+N this month` | `GET /api/clients/` — count |
| Active Audits | Audits with status ≠ COMPLETE and ≠ DELIVERED | `N in PROCESSING` | `GET /api/audits/` |
| Avg. Compliance Score | Mean of all `compliance_score` where status = COMPLETE | `across N audits` | Computed client-side |
| Open Critical Gaps | Count of `ComplianceGap` where `severity=CRITICAL` and `addressed=false` | `across all clients` | `GET /api/gaps/` filtered |

Design: White cards, colored left-border accent, large number (32px), trend arrow (up/down) if data supports it.

#### 6.1.2 Audit Pipeline (Kanban-style row)

Six columns, one per status. Each column shows:
- Status name + color badge
- Count of audits in that status
- Stack of mini-cards (max 3 visible, then "+N more" link)

Each mini-card shows:
- Client company name (bold)
- Tier badge (T1/T2/T3)
- Time in status (e.g., "3 days")
- For PROCESSING/ANALYSIS: a spinner or progress bar

#### 6.1.3 Recent Activity Feed (right panel)

Chronological list of last 20 events:
- "✅ Audit for [Company] completed — score 74%"
- "⚠️ [Company] audit moved to REVIEW — manual check needed"
- "📄 New document uploaded for [Company]"
- "🚨 3 CRITICAL gaps found for [Company]"

Each entry: icon, message, relative timestamp ("2 hours ago").

#### 6.1.4 Compliance Score Distribution (chart)

Bar chart or histogram:
- X-axis: Score ranges (0-20, 20-40, 40-60, 60-80, 80-100)
- Y-axis: Number of audits
- Color: Red → Yellow → Green gradient
- Label: "Distribution across N completed audits"

#### 6.1.5 Gaps by Category (chart)

Horizontal bar chart:
- Categories: TECHNICAL, ORGANIZATIONAL, INCIDENT_RESPONSE, SUPPLY_CHAIN, ACCESS_CONTROL, LOGGING, TRAINING, GOVERNANCE
- Bars stacked by severity (CRITICAL=red, HIGH=orange, MEDIUM=yellow, LOW=slate)
- Shows which NIS2 area is most problematic across all clients

#### 6.1.6 Revenue Summary (bottom card — visible to Admin only)

| Metric | Value |
|--------|-------|
| Quoted this month | €XX,XXX |
| Paid invoices | €XX,XXX |
| Unpaid | €XX,XXX |
| Outstanding audits | N |

---

### 6.2 Clients List

**Route:** `/clients`
**Purpose:** Browse and manage all client companies.

#### Layout: Table with sidebar filter panel

**Filter sidebar (left, collapsible):**
- Sector (multi-select checkboxes): MSP, HOSTING, CLOUD, TRANSPORT, ENERGY, HEALTHCARE, FINANCE, TELECOM, OTHER
- Company size: SMALL / MEDIUM / LARGE
- Has active audit: Yes / No
- Account manager (Admin only)

**Table columns:**

| Column | Content | Sortable |
|--------|---------|----------|
| Company | Company name (bold) + city below | Yes |
| KVK | KVK number in monospace | No |
| Sector | Badge with sector label | Yes |
| Size | SMALL / MEDIUM / LARGE badge | No |
| Audits | Count of audits, with latest status badge | No |
| Latest Score | Compliance score with color indicator (green/yellow/red) | Yes |
| Contact | Contact person name + email icon | No |
| Actions | View / New Audit buttons | No |

**Empty state:** Illustration + "No clients yet. Add your first client →" button.

**Top bar:**
- Search input (searches company_name, kvk_number, contact_person)
- "+ New Client" primary button (right)

**Row click:** Navigate to `/clients/:id`

---

### 6.3 Client Detail

**Route:** `/clients/:id`
**Purpose:** Full profile of one client company + all their audits.

#### Layout: Two-column (70/30)

**Left column:**

**Client Info card:**
- Company name (H1, large)
- KVK badge (monospace)
- Sector + Size badges
- Address block (street, city, postal)
- Contact person + email + phone
- Account manager name
- Member since date

**Edit button** (top right of card) → inline edit form

**Audit History table:**

| Column | Content |
|--------|---------|
| Date | Created date (DD-MM-YYYY) |
| Tier | T1 / T2 / T3 badge |
| Status | Colored status badge |
| Score | Compliance % with color bar |
| Gaps | Number found (CRITICAL count in red) |
| Duration | X days (or "—" if not complete) |
| Paid | ✓ or pending |
| Actions | View / Download Report |

**Right column:**

**Compliance Trend card:**
- Line chart: X = audit dates, Y = compliance score (0–100)
- Shows improvement over time
- Only visible if ≥ 2 completed audits

**Sector Context card:**
- "For a [sector] company of [size], the average compliance score is XX%"
- (Computed from all clients in same sector/size)

**Quick Actions card:**
- "Start New Audit" button → opens New Audit modal pre-filled with this client
- "Download Latest Report" button (only if report exists)

---

### 6.4 New Client Form

**Route:** `/clients/new` (or modal)
**Purpose:** Onboard a new Dutch IT company.

**Form fields:**

| Field | Type | Validation |
|-------|------|------------|
| Company Name | Text | Required, max 200 chars |
| KVK Number | Text | Required, exactly 8 digits, unique |
| Sector | Select dropdown | Required |
| Company Size | Radio (SMALL / MEDIUM / LARGE) | Required |
| Contact Person | Text | Required |
| Email | Email | Required, valid email |
| Phone | Text | Optional, Dutch format hint |
| Address | Textarea | Required |
| City | Text | Required |
| Postal Code | Text | Required, Dutch format (1234 AB) |

**Submit:** POST to `/api/clients/` → redirect to client detail page.

**KVK validation:** Real-time format check (8 digits). Error: "KVK-nummer moet 8 cijfers bevatten."

---

### 6.5 Audits List

**Route:** `/audits`
**Purpose:** Global view of all audits across all clients.

#### Layout: Table + filter bar (top)

**Filter bar (horizontal, above table):**
- Status filter: All / INTAKE / PROCESSING / ANALYSIS / REVIEW / COMPLETE / DELIVERED (pill tabs)
- Tier filter: All / T1 / T2 / T3
- Date range picker
- Search: by client name

**Table columns:**

| Column | Content | Sortable |
|--------|---------|----------|
| Client | Company name + sector badge | Yes |
| Tier | T1 / T2 / T3 with price | No |
| Status | Colored animated badge | Yes |
| Score | % + color bar (empty if not complete) | Yes |
| Gaps | Total / CRITICAL count (e.g., "12 / 3 critical") | Yes |
| Documents | Count uploaded | No |
| Created | Date + "X days ago" | Yes |
| Duration | Days from start to complete (or ongoing) | No |
| Paid | ✓ euro sign / pending | No |
| Actions | View / Start / Download | No |

**PROCESSING rows:** Show a subtle amber pulsing background + spinner in status column.
**REVIEW rows:** Show orange highlight + "Needs attention" tooltip.

---

### 6.6 Audit Detail

**Route:** `/audits/:id`
**Purpose:** The most important screen. Full audit workspace.

#### Layout: Header + tabbed content

**Header bar:**
- Client name (H1) + company size + sector
- Audit tier badge (T1/T2/T3)
- Status badge (large, colored, animated if PROCESSING)
- Compliance score gauge (circular, 0–100, color = red/yellow/green)
- "Start Processing" button (only if status = INTAKE)
- "Download Report" button (only if report_generated = true)
- Created / Started / Completed timestamps

**Compliance Score Gauge:**
- Large circular arc gauge (like a speedometer)
- 0–40: Red zone
- 40–70: Yellow/amber zone
- 70–100: Green zone
- Center number: e.g., "74%" in large bold
- Label below: "Compliance Score"
- Hidden with placeholder ("—") until status = COMPLETE

---

#### Tab 1: Overview

**Executive Summary card** (only after COMPLETE):
- White card with blue left border
- Claude's generated `summary` text (prose paragraph)
- "Top 3 Priorities" as numbered list with warning icons

**Gap Severity Breakdown:**
- Four stat boxes in a row: CRITICAL (red) / HIGH (orange) / MEDIUM (yellow) / LOW (slate)
- Each shows count + "gaps"
- Click a box → filters the gap table below

**Gap Category Heatmap:**
- 8 categories as squares in a grid
- Color intensity = number of gaps in that category
- Size = risk severity weighting
- Click → filters gap list to that category

**Remediation Effort Summary:**
- Total estimated hours: XX hours
- Total estimated cost: €XX,XXX (if cost data available)
- "At current rate this is X months of work"

---

#### Tab 2: Gap Analysis

**Purpose:** Detailed, filterable table of all ComplianceGap records.

**Filter bar:**
- Severity: All / CRITICAL / HIGH / MEDIUM / LOW (pill tabs)
- Category: dropdown multi-select
- Addressed: All / Open / Resolved
- Search: text search in title + description

**Gap table:**

| Column | Content |
|--------|---------|
| Severity | Colored badge (CRITICAL/HIGH/MEDIUM/LOW) |
| Title | Gap title (bold, clickable to expand) |
| NIS2 Article | e.g., "Art. 21.2" in a code chip |
| Category | Category badge |
| Risk Score | 1–10 with color dot |
| Effort | Est. hours (e.g., "40h") |
| Status | Open (red dot) / Resolved (green check) |
| Actions | Mark Resolved / View Details |

**Row expand (accordion):** Click a row to expand inline detail:
- **Current State** (what the client has now)
- **Required State** (what NIS2 demands)
- **Recommendation** (what to do)
- **Business Impact**
- **Implementation Notes** (editable textarea, PATCH to API)
- **Mark as Addressed** toggle → sets `addressed=true`, `addressed_date=today`

**Export button:** Download gap list as CSV (client-side generation from API data).

---

#### Tab 3: Documents

**Purpose:** Manage all uploaded client documents for this audit.

**Upload zone (top):**
- Large dashed drag-and-drop area
- "Drop PDF, DOCX, or TXT files here (max 50MB)"
- Or click to browse files
- Document type selector (required before upload): dropdown with all 9 types
- POST to `/api/documents/` with multipart form

**Documents table:**

| Column | Content |
|--------|---------|
| File | Filename (with file type icon: PDF/DOCX/TXT) |
| Type | Document type badge |
| Size | Human-readable (e.g., "2.4 MB") |
| Pages | Page count (or "—" if not extracted) |
| Security | Virus scan status + PII status |
| Relevance | Score bar (0–100, only if available) |
| Uploaded | Date + uploaded by |
| Actions | Process / Delete |

**Security status icons:**
- Virus scan: 🔍 Pending / ✅ Clean / 🚫 Threat Found
- PII: 🔍 Pending / ✅ None / ⚠️ Detected / 🔒 Anonymized

**Process button:** POST to `/api/documents/:id/process/` → updates security fields.

---

#### Tab 4: Timeline

**Purpose:** Visual audit history — what happened and when.

**Vertical timeline:**

```
○ Audit Created
  [date + time]
  Tier T1 — €950 quoted

○ Document Uploaded: security-policy.pdf
  [date + time]
  Uploaded by [user]

● Processing Started
  [date + time]
  Triggered by [user]

● Gap Analysis Completed
  [date + time]
  12 gaps found — compliance score 74%
  Claude Sonnet 4 · 20 NIS2 requirements retrieved

○ Report Generated
  [date + time]
  PDF available for download

○ Delivered to Client
  [date + time]
  Invoice paid ✓
```

Each node: icon (circle, filled=done, empty=pending), label, timestamp, optional detail text.

---

### 6.7 Gap Browser (Global)

**Route:** `/gaps`
**Purpose:** Cross-client gap analysis. Find systemic issues across all audits.

**Top KPI bar:**

| Metric | Value |
|--------|-------|
| Total open gaps | N |
| Critical unaddressed | N (red) |
| Avg. risk score | X.X / 10 |
| Total remediation hours | XXXX h |

**Treemap chart:**
- Size = gap count per category
- Color = avg. severity in that category
- Click a category → filter table below

**Gap table** (same as audit detail tab 2, but across all audits):
- Extra column: **Client** (which company this gap belongs to)
- Extra column: **Audit** (link to specific audit)
- Useful for spotting: "All MSP clients are missing incident response plans"

---

### 6.8 Processing / Live Status View

**Triggered when:** User clicks "Start Processing" on an audit.

**Behavior:**
- Button click → POST to `/api/audits/:id/start_processing/`
- UI immediately transitions to a live status card:

```
┌──────────────────────────────────────────────────────────────┐
│  🤖 AI Analysis in Progress                                  │
│                                                              │
│  ✅  Step 1: Documents loaded (3 files, 47 pages)            │
│  ✅  Step 2: Querying NIS2 knowledge base (20 results)       │
│  ⟳   Step 3: Claude Sonnet analyzing compliance gaps...      │
│  ○   Step 4: Saving results to database                      │
│  ○   Step 5: Generating compliance score                     │
│                                                              │
│  Status: ANALYSIS                           [Cancel]         │
└──────────────────────────────────────────────────────────────┘
```

- Poll `GET /api/audits/:id/` every 3 seconds
- Update step indicators based on status transitions:
  - PROCESSING → step 1–2 complete
  - ANALYSIS → step 3 active
  - COMPLETE → all steps done → reveal score with animation
  - REVIEW → show error state with red banner

**Completion animation:**
- Score gauge animates from 0 to final value (e.g., 74%)
- Confetti or success banner: "Analysis complete — 12 gaps identified"
- Auto-scroll to Overview tab

---

## 7. Component Library

These reusable components should be built first:

### 7.1 StatusBadge
- Props: `status` (INTAKE | PROCESSING | ANALYSIS | REVIEW | COMPLETE | DELIVERED)
- Renders: colored pill badge with label
- PROCESSING variant: pulsing amber animation

### 7.2 SeverityBadge
- Props: `severity` (CRITICAL | HIGH | MEDIUM | LOW)
- Renders: colored pill with label and icon

### 7.3 ComplianceGauge
- Props: `score` (0–100 | null), `size` (sm | md | lg)
- Renders: circular arc gauge
- Null state: renders as "—" placeholder

### 7.4 GapTable
- Props: `gaps[]`, `showClient` (bool), filters
- Reusable in both audit detail and global gap browser

### 7.5 DocumentUploader
- Drag-and-drop zone + file type selector + progress bar
- Calls POST `/api/documents/`

### 7.6 AuditCard (for Kanban/pipeline)
- Mini card with: client name, tier badge, time in status
- Click → navigate to `/audits/:id`

### 7.7 TimelineEvent
- Icon (filled/empty circle), label, timestamp, optional description

---

## 8. API Integration Map

| Screen | API Calls |
|--------|-----------|
| Dashboard | `GET /api/clients/`, `GET /api/audits/`, `GET /api/gaps/` |
| Clients List | `GET /api/clients/` |
| Client Detail | `GET /api/clients/:id`, `GET /api/audits/?client=:id` |
| New Client | `POST /api/clients/` |
| Audits List | `GET /api/audits/` |
| Audit Detail | `GET /api/audits/:id`, `GET /api/gaps/?audit_id=:id`, `GET /api/documents/?audit=:id` |
| Start Processing | `POST /api/audits/:id/start_processing/`, then poll `GET /api/audits/:id/` |
| Upload Document | `POST /api/documents/` (multipart) |
| Process Document | `POST /api/documents/:id/process/` |
| Download Report | `GET /api/audits/:id/download_report/` |
| Mark Gap Resolved | `PATCH /api/gaps/:id/` with `{addressed: true, addressed_date: today}` |

---

## 9. Real-time Polling Strategy

Since the backend is synchronous (no WebSocket), use client-side polling:

```
Polling intervals:
  - Status = PROCESSING or ANALYSIS: poll every 3 seconds
  - Status = REVIEW or COMPLETE: stop polling, show result
  - Timeout after 10 minutes: show error state

Implementation:
  - Start polling when "Start Processing" button clicked
  - Stop polling when status changes to COMPLETE or REVIEW
  - Show elapsed time: "Analysis running for 1m 23s"
```

---

## 10. Responsive Design

| Breakpoint | Layout |
|------------|--------|
| Desktop (≥1280px) | Full sidebar + two-column content |
| Tablet (768–1279px) | Collapsed sidebar (icon-only) + single column |
| Mobile (<768px) | Bottom navigation + stacked cards |

The primary use case is desktop (consultants at their desk), but tablet must work for demos with clients.

---

## 11. Dutch Localization Requirements

- All currency: `€1.250,00` format (Dutch: period as thousands separator, comma as decimal)
- All dates: `23-02-2026` (DD-MM-YYYY)
- KVK label: "KVK-nummer" (not "registration number")
- Audit status labels in Dutch where shown to clients:
  - INTAKE → "Documenten uploaden"
  - PROCESSING → "Verwerking"
  - COMPLETE → "Gereed"
  - DELIVERED → "Opgeleverd"
- Company size labels: "Klein (10–49)", "Middel (50–249)", "Groot (250+)"

---

## 12. Suggested Tech Stack

The dashboard should be a standalone SPA that communicates with the Django REST API:

| Layer | Recommendation | Reason |
|-------|---------------|--------|
| Framework | React 19 or Vue 3 | Both work; React has larger ecosystem |
| Styling | Tailwind CSS | Fast utility-first, great for dashboards |
| Component lib | shadcn/ui (React) or PrimeVue (Vue) | Pre-built accessible components |
| Charts | Recharts (React) or Chart.js | Compliance gauges, bar charts, treemaps |
| State | Zustand (React) or Pinia (Vue) | Simple, no boilerplate |
| HTTP | Axios or TanStack Query | Auto polling, caching, loading states |
| Icons | Lucide React | Clean, consistent icon set |

Django CORS is already configured for `localhost:3000` and `localhost:5173`, so the SPA can run on Vite's default port immediately.

---

## 13. Screen Priority (Build Order)

| Priority | Screen | Why |
|----------|--------|-----|
| 1 | Audit Detail (tabs 1–3) | Core value — this is what consultants use daily |
| 2 | Dashboard home | First screen seen, shows business health |
| 3 | Clients List + Detail | Client management |
| 4 | Audits List | Audit pipeline overview |
| 5 | New Client form | Onboarding |
| 6 | Gap Browser (global) | Nice-to-have analytics |
| 7 | Timeline tab | Nice-to-have polish |

---

## 14. Out of Scope (Phase 3)

- Client portal (clients logging in to view their own reports)
- Stripe payment integration
- Email notifications (audit complete, report ready)
- Multi-language support (only Dutch + English for now)
- Mobile app

---

## 15. Success Metrics

| Metric | Target |
|--------|--------|
| Time to create audit + upload docs | < 2 minutes |
| Time to find a specific gap across all clients | < 30 seconds |
| Processing status visible without page refresh | Always (polling) |
| Report download in < 3 clicks from audit detail | Always |
| Zero confusion about audit status | Status badge visible on every view |
