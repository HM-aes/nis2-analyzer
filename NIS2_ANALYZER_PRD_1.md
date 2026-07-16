# NIS2 Compliance Analyzer — Complete Missing Features PRD
# Version: 1.0 | Date: May 2026 | Owner: AES AI Solutions
# Instructions for Claude Code:
# Read this entire file first, then implement each TASK in order.
# Complete all acceptance criteria before moving to next task.
# Run migrations after any model changes.
# Test each endpoint before marking task complete.

---

## CONTEXT & STACK

- Django 6.0
- Pydantic AI + Claude Sonnet 4 agents
- Qdrant vector database (NIS2 knowledge base)
- ReportLab 4.0.9 (PDF generation)
- Plotly + Matplotlib (charts)
- Alpine.js + HTMX (frontend interactions)
- HTML/CSS dashboard (no React/Vue)
- Existing apps: compliance_engine, nis2_agents, rag_engine
- New app to create: report_generator
- Database: PostgreSQL (psycopg2-binary installed)
- All templates use Dutch language (keep consistent)

---

## TASK 1 — Add Country Field to Client Model

### What
Add country field to Client model to enable
country-specific NIS2 requirements in reports.
NIS2 is implemented differently per EU member state.

### Files to modify
- compliance_engine/models.py
- compliance_engine/migrations/ (create new migration)
- dashboard/templates/dashboard/client_new.html
- dashboard/templates/dashboard/client_detail.html

### Model change
```python
COUNTRY_CHOICES = [
    ('NL', 'Netherlands'),
    ('DE', 'Germany'),
    ('BE', 'Belgium'),
    ('FR', 'France'),
    ('ES', 'Spain'),
    ('IT', 'Italy'),
    ('PL', 'Poland'),
    ('SE', 'Sweden'),
    ('DK', 'Denmark'),
    ('FI', 'Finland'),
    ('AT', 'Austria'),
    ('IE', 'Ireland'),
    ('GB', 'United Kingdom'),
    ('OTHER', 'Other EU'),
]

country = models.CharField(
    max_length=10,
    choices=COUNTRY_CHOICES,
    default='NL'
)
```

### Template requirements
- Add country dropdown to client_new.html form
  in the company info section
- Display country in client_detail.html info panel
- Include country in client edit form

### Acceptance criteria
- [ ] Country field added to Client model
- [ ] Migration created and applied successfully
- [ ] Country dropdown renders in client_new.html
- [ ] Country visible in client_detail.html
- [ ] Existing clients default to NL without errors

---

## TASK 2 — Audit Creation View

### What
Consultants cannot create audits from the dashboard UI.
Only the REST API works currently.
The "+ Nieuwe Audit Starten" button on client_detail.html
links to a non-existent route. Fix this completely.

### Files to create
- dashboard/templates/dashboard/audit_new.html

### Files to modify
- dashboard/views.py (add NewAuditView class)
- dashboard/urls.py (add audit_new URL pattern)
- dashboard/templates/dashboard/client_detail.html
  (wire the existing button to new URL)

### View logic
```python
class NewAuditView(LoginRequiredMixin, View):
    def get(self, request):
        clients = Client.objects.all().order_by('company_name')
        # Pre-select client if client_id in query params
        selected_client_id = request.GET.get('client_id')
        return render(request, 'dashboard/audit_new.html', {
            'clients': clients,
            'tier_choices': ComplianceAudit.TIER_CHOICES,
            'selected_client_id': selected_client_id,
        })

    def post(self, request):
        client_id = request.POST.get('client')
        tier = request.POST.get('tier')
        quoted_price = request.POST.get('quoted_price')

        if not all([client_id, tier, quoted_price]):
            messages.error(request, 'All fields are required')
            return redirect('dashboard:audit_new')

        audit = ComplianceAudit.objects.create(
            client_id=client_id,
            tier=tier,
            quoted_price=quoted_price,
            status='INTAKE',
        )
        messages.success(request,
            f'Audit aangemaakt voor {audit.client.company_name}')
        return redirect('dashboard:audit_detail', pk=audit.pk)
```

### Tier pricing (auto-fill quoted_price via Alpine.js)
```javascript
// In audit_new.html Alpine.js component
tierPrices = { 'T1': 950, 'T2': 2500, 'T3': 5000 }
```

### Template requirements
- Client dropdown — searchable, pre-selects if client_id param present
- Tier radio buttons showing T1/T2/T3 with description and price
- Quoted price field — auto-filled by tier selection, editable
- Submit button with loading state (Alpine.js x-data running=false)
- Cancel link back to audits list
- Form validation — all fields required
- Consistent styling with existing dashboard forms

### URL
```python
path('audits/new/', NewAuditView.as_view(), name='audit_new'),
```

### Wire up existing button
In client_detail.html find the "+ Nieuwe Audit Starten" button
and update href to:
```
{% url 'dashboard:audit_new' %}?client_id={{ client.pk }}
```

### Acceptance criteria
- [ ] GET renders form with all fields
- [ ] Client pre-selected when client_id query param present
- [ ] Tier selection auto-fills quoted price via Alpine.js
- [ ] POST creates ComplianceAudit with status INTAKE
- [ ] Redirects to audit_detail after creation
- [ ] Success toast message displayed
- [ ] Submit button shows loading state on click
- [ ] Cancel returns to audits list
- [ ] Validation errors shown inline

---

## TASK 3 — Client Edit View

### What
Alpine.js edit toggle (x-data="{ editing: false }") exists
in client_detail.html but there is no backend POST route
or form action. The edit button toggles display only.
Wire it up completely.

### Files to modify
- dashboard/views.py (add ClientUpdateView)
- dashboard/urls.py (add client_update URL)
- dashboard/templates/dashboard/client_detail.html
  (add form action, method, all input fields in edit mode)

### View logic
```python
class ClientUpdateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        client = get_object_or_404(Client, pk=pk)
        client.company_name = request.POST.get(
            'company_name', client.company_name)
        client.sector = request.POST.get(
            'sector', client.sector)
        client.company_size = request.POST.get(
            'company_size', client.company_size)
        client.contact_person = request.POST.get(
            'contact_person', client.contact_person)
        client.email = request.POST.get(
            'email', client.email)
        client.country = request.POST.get(
            'country', client.country)
        client.save()
        messages.success(request, 'Client bijgewerkt')
        return redirect('dashboard:client_detail', pk=pk)
```

### Template requirements
- Edit form wraps all editable fields
- Form action POST to client_update URL
- Include {% csrf_token %}
- Fields: company_name, sector (select), company_size
  (select), contact_person, email, country (select)
- KVK field displayed but NOT editable (read-only)
- Save button + Cancel button (sets editing=false)
- Cancel does NOT submit form
- Match existing input styling

### URL
```python
path('clients/<uuid:pk>/edit/',
    ClientUpdateView.as_view(),
    name='client_update'),
```

### Acceptance criteria
- [ ] Edit toggle shows input fields
- [ ] All fields editable except KVK number
- [ ] POST saves changes to database
- [ ] Redirects back to client_detail
- [ ] Success toast shown
- [ ] Cancel returns to display mode without saving

---

## TASK 4 — Audit Status Transition Actions

### What
Audits that reach REVIEW or COMPLETE status are stuck.
No UI exists to advance the pipeline:
REVIEW → COMPLETE → DELIVERED
Also need ability to reset failed audits back to INTAKE.

### Files to modify
- dashboard/views.py (add AuditTransitionView)
- dashboard/urls.py (add transition URL)
- dashboard/templates/dashboard/audit_detail.html
  (add transition buttons per status)

### View logic
```python
VALID_TRANSITIONS = {
    'REVIEW': ['COMPLETE', 'INTAKE'],
    'COMPLETE': ['DELIVERED', 'INTAKE'],
    'DELIVERED': [],
    'INTAKE': ['PROCESSING'],
    'PROCESSING': ['INTAKE'],
    'ANALYSIS': ['INTAKE'],
    'ERROR': ['INTAKE'],
}

class AuditTransitionView(LoginRequiredMixin, View):
    def post(self, request, pk):
        audit = get_object_or_404(ComplianceAudit, pk=pk)
        target_status = request.POST.get('status')

        if target_status not in VALID_TRANSITIONS.get(
                audit.status, []):
            messages.error(request, 'Ongeldige statusovergang')
            return redirect('dashboard:audit_detail', pk=pk)

        audit.status = target_status
        if target_status == 'DELIVERED':
            audit.delivered_at = timezone.now()
        if target_status == 'COMPLETE':
            audit.completed_at = timezone.now()
        audit.save()
        messages.success(request,
            f'Status bijgewerkt naar {target_status}')
        return redirect('dashboard:audit_detail', pk=pk)
```

### Template requirements
Add action buttons to audit_detail.html
conditionally shown by status:

```
Status REVIEW:
  - "Analyse Goedkeuren" button → POST status=COMPLETE
  - "Opnieuw Starten" button → POST status=INTAKE

Status COMPLETE:
  - "Rapport Geleverd" button → POST status=DELIVERED
  - "Opnieuw Starten" button → POST status=INTAKE

Status ERROR or PROCESSING:
  - "Reset naar Intake" button → POST status=INTAKE
```

Each button must have:
- Confirmation modal (Alpine.js) before submitting
- CSRF token in form
- Appropriate color (green=approve, red=reset, blue=deliver)

### URL
```python
path('audits/<uuid:pk>/transition/',
    AuditTransitionView.as_view(),
    name='audit_transition'),
```

### Acceptance criteria
- [ ] Correct buttons shown per audit status
- [ ] Confirmation modal before each transition
- [ ] Status updates correctly in database
- [ ] Timestamps set on COMPLETE and DELIVERED
- [ ] Invalid transitions rejected with error message
- [ ] Success toast shown after transition
- [ ] Audit detail page reflects new status immediately

---

## TASK 5 — Gap Mark-as-Addressed

### What
Gaps are the core deliverable but consultants cannot
mark them as addressed after client remediation.
The addressed filter pill in gaps.html is decorative only.
Build the full workflow.

### Files to modify
- dashboard/views.py (add GapAddressView)
- dashboard/urls.py (add gap_address URL)
- dashboard/templates/dashboard/gaps.html
  (add mark-addressed form to expanded gap rows)
- dashboard/templates/dashboard/gap_rows.html
  (verify exists, add addressed action if missing)

### View logic
```python
class GapAddressView(LoginRequiredMixin, View):
    def post(self, request, pk):
        gap = get_object_or_404(ComplianceGap, pk=pk)
        gap.addressed = True
        gap.addressed_date = timezone.now().date()
        gap.implementation_notes = request.POST.get(
            'implementation_notes', '')
        gap.save()

        # Return updated row partial for HTMX swap
        return render(request,
            'dashboard/partials/gap_row.html',
            {'gap': gap})
```

### Template requirements
In the expanded gap row (x-data="{ expanded: false }"):

Add third panel below current/required state:
```html
<!-- Mark as Addressed panel -->
<div x-show="!gap.addressed">
  <form hx-post="{% url 'dashboard:gap_address' gap.pk %}"
        hx-target="closest tr"
        hx-swap="outerHTML">
    {% csrf_token %}
    <textarea name="implementation_notes"
      placeholder="Beschrijf de uitgevoerde maatregelen...">
    </textarea>
    <button type="submit">
      Markeer als Opgelost
    </button>
  </form>
</div>

<!-- Addressed status display -->
<div x-show="gap.addressed">
  ✅ Opgelost op {{ gap.addressed_date }}
  <p>{{ gap.implementation_notes }}</p>
</div>
```

Also create:
- dashboard/templates/dashboard/partials/gap_row.html
  (HTMX partial for single gap row after addressing)

### URL
```python
path('gaps/<uuid:pk>/address/',
    GapAddressView.as_view(),
    name='gap_address'),
```

### Acceptance criteria
- [ ] Mark-addressed form visible in expanded gap row
- [ ] Implementation notes textarea works
- [ ] POST sets addressed=True, addressed_date, notes
- [ ] HTMX updates row without page reload
- [ ] Addressed gaps show green resolved indicator
- [ ] Addressed filter pill in gaps.html now works
- [ ] Gap count in KPI bar updates correctly

---

## TASK 6 — Audit Detail Tab 3 (Documents)

### What
Documents tab in audit_detail.html is unbuilt.
Clients need to see uploaded documents, their
processing status, and security flags.

### Files to create
- dashboard/templates/dashboard/partials/document_list.html

### Files to modify
- dashboard/views.py (add DocumentDeleteView,
  DocumentReprocessView)
- dashboard/urls.py (add document URLs)
- dashboard/templates/dashboard/audit_detail.html
  (wire Tab 3 content)

### Tab 3 template requirements
For each ClientDocument show:
- Filename with file type icon (PDF/DOCX/TXT)
- document_type badge (POLICY / PROCEDURE / etc)
- File size (human readable)
- Upload date (relative: "2 days ago")
- Processing status badge:
  PENDING=grey, PROCESSING=blue spinner,
  COMPLETED=green, FAILED=red
- Security flags row:
  - virus_scanned: ✅ Clean / ⚠️ Not scanned / 🚨 Threat
  - pii_detected: ✅ No PII / ⚠️ PII Found
  - language_detected: flag emoji + language name
- Actions: Delete button, Reprocess button (if FAILED)

### Delete view
```python
class DocumentDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        doc = get_object_or_404(ClientDocument, pk=pk)
        # Only allow delete if audit not PROCESSING
        if doc.audit.status == 'PROCESSING':
            messages.error(request,
                'Kan document niet verwijderen tijdens verwerking')
            return redirect('dashboard:audit_detail',
                pk=doc.audit.pk)
        doc.file.delete(save=False)
        doc.delete()
        messages.success(request, 'Document verwijderd')
        return redirect('dashboard:audit_detail',
            pk=doc.audit.pk)
```

### URLs
```python
path('documents/<uuid:pk>/delete/',
    DocumentDeleteView.as_view(),
    name='document_delete'),
path('documents/<uuid:pk>/reprocess/',
    DocumentReprocessView.as_view(),
    name='document_reprocess'),
```

### Acceptance criteria
- [ ] Tab 3 renders document list
- [ ] All security flags displayed with correct icons
- [ ] Delete button removes document and file
- [ ] Cannot delete during active processing
- [ ] Reprocess triggers docling extraction again
- [ ] Empty state shown when no documents uploaded
- [ ] Document count badge on tab header

---

## TASK 7 — Audit Detail Tab 4 (Timeline)

### What
Timeline tab exists in navigation but has no content.
Show chronological audit history assembled from
existing model timestamps. No new model needed.

### Files to modify
- dashboard/views.py (add timeline context to
  AuditDetailView)
- dashboard/templates/dashboard/audit_detail.html
  (build Tab 4 content)

### Timeline events to show (assembled from existing data)
```python
def build_audit_timeline(audit, gaps, documents):
    events = []

    # Audit lifecycle events
    events.append({
        'timestamp': audit.created_at,
        'type': 'created',
        'icon': '📋',
        'title': 'Audit aangemaakt',
        'detail': f'Tier {audit.tier} — €{audit.quoted_price}'
    })

    for doc in documents:
        events.append({
            'timestamp': doc.uploaded_at,
            'type': 'document',
            'icon': '📄',
            'title': f'Document geüpload',
            'detail': doc.original_filename
        })

    if audit.started_at:
        events.append({
            'timestamp': audit.started_at,
            'type': 'processing',
            'icon': '🤖',
            'title': 'AI analyse gestart',
            'detail': 'Claude NIS2 analyse actief'
        })

    for gap in gaps.order_by('created_at'):
        events.append({
            'timestamp': gap.created_at,
            'type': 'gap',
            'icon': '⚠️' if gap.severity == 'HIGH'
                    else '🔴' if gap.severity == 'CRITICAL'
                    else '🟡',
            'title': f'Gap gevonden: {gap.title}',
            'detail': f'{gap.severity} — {gap.category}'
        })

    if audit.completed_at:
        events.append({
            'timestamp': audit.completed_at,
            'type': 'completed',
            'icon': '✅',
            'title': 'Analyse voltooid',
            'detail': f'Score: {audit.compliance_score}%'
        })

    if audit.delivered_at:
        events.append({
            'timestamp': audit.delivered_at,
            'type': 'delivered',
            'icon': '🚀',
            'title': 'Rapport geleverd aan klant',
            'detail': ''
        })

    return sorted(events,
        key=lambda x: x['timestamp'], reverse=True)
```

### Template requirements
- Vertical timeline with connector line
- Each event: icon + title + detail + relative timestamp
- Color coded by event type
- Most recent at top
- Smooth styling consistent with dashboard

### Acceptance criteria
- [ ] Tab 4 renders timeline with all events
- [ ] Events sorted newest first
- [ ] Document uploads shown with filename
- [ ] Gaps shown with severity icon
- [ ] All audit lifecycle timestamps shown
- [ ] Empty state if audit just created

---

## TASK 8 — Report Generator App (Core)

### What
Create new Django app: report_generator
This is the most important feature for revenue.
Two report types:
  Type 1: Sector Requirements Report (no docs needed)
  Type 2: Gap Analysis Report (post-audit, paid product)

### Create new Django app
```bash
python manage.py startapp report_generator
```

Add to INSTALLED_APPS in settings.py:
```python
'report_generator',
```

### Files to create
- report_generator/__init__.py
- report_generator/apps.py
- report_generator/views.py
- report_generator/urls.py
- report_generator/generator.py (core PDF logic)
- report_generator/claude_prompts.py (AI prompts)
- report_generator/charts.py (Plotly chart generation)
- report_generator/templates/report_generator/
    sector_report.html (form page)

### Wire into main urls.py
```python
path('reports/', include('report_generator.urls')),
```

### Acceptance criteria
- [ ] App created and registered in INSTALLED_APPS
- [ ] URLs included in main urls.py
- [ ] App structure created (all files exist)

---

## TASK 9 — Report Generator: Claude Prompts

### What
Define all Claude prompts used in report generation.
Keep prompts in one file for easy maintenance.

### File: report_generator/claude_prompts.py

```python
"""
All Claude prompts for NIS2 report generation.
Prompts are structured for Pydantic AI agents.
"""

SECTOR_REPORT_SYSTEM = """
You are an expert NIS2 compliance consultant.
You generate professional compliance reports for
organisations in the EU. Your reports are precise,
actionable, and based on the actual NIS2 Directive
(EU) 2022/2555. Always cite specific articles.
Respond in English unless instructed otherwise.
Format all output as clean prose suitable for
a professional PDF report.
"""

SECTOR_REQUIREMENTS_PROMPT = """
Generate a comprehensive NIS2 compliance requirements
report for the following organisation:

Company: {company_name}
Sector: {sector}
Country: {country}
Entity Classification: {entity_type}
Company Size: {company_size}

Based on NIS2 Directive (EU) 2022/2555, provide:

1. ENTITY CLASSIFICATION
   Confirm whether this organisation is an Essential
   Entity or Important Entity under Article 3.
   Explain the classification criteria that apply.

2. MANDATORY REQUIREMENTS (Article 21)
   List all 10 mandatory cybersecurity risk management
   measures that apply to this sector. For each:
   - Requirement description
   - What evidence regulators expect
   - Typical implementation approach

3. INCIDENT REPORTING OBLIGATIONS (Article 23)
   Explain the 24-hour early warning requirement,
   72-hour notification, and monthly final report.
   Include country-specific reporting authority
   for {country}.

4. GOVERNANCE REQUIREMENTS (Article 20)
   Explain board and executive accountability
   obligations. Include personal liability risks.

5. SUPPLY CHAIN SECURITY (Article 21.2d)
   Requirements specific to {sector} supply chain.

6. COUNTRY-SPECIFIC REQUIREMENTS
   Additional requirements under {country} national
   transposition of NIS2.

7. PENALTIES
   Maximum fines for Essential vs Important entities.
   Personal liability for executives.

8. RECOMMENDED NEXT STEPS
   Prioritised action list for this sector and size.

Write in professional English suitable for a board
presentation. Be specific, not generic.
"""

EXECUTIVE_SUMMARY_PROMPT = """
Write a professional executive summary for a NIS2
gap analysis report for the following organisation:

Company: {company_name}
Sector: {sector}
Compliance Score: {compliance_score}%
Total Gaps: {total_gaps}
Critical Gaps: {critical_gaps}
High Gaps: {high_gaps}
Medium Gaps: {medium_gaps}
Low Gaps: {low_gaps}
Total Remediation Hours: {remediation_hours}
Estimated Remediation Cost: €{remediation_cost}

Key gaps found:
{top_gaps_summary}

Write 3-4 paragraphs covering:
1. Overall compliance posture and score interpretation
2. Most critical findings requiring immediate action
3. Remediation effort and timeline overview
4. Risk to the organisation if gaps not addressed

Tone: Professional, direct, board-level audience.
Do not use bullet points. Prose only.
Maximum 400 words.
"""

REMEDIATION_ROADMAP_PROMPT = """
Create a prioritised remediation roadmap for this
NIS2 gap analysis:

Gaps (JSON):
{gaps_json}

Organisation:
- Sector: {sector}
- Size: {company_size}
- Country: {country}

Create a 3-phase roadmap:
PHASE 1 (0-30 days): Critical and quick wins
PHASE 2 (30-90 days): High severity gaps
PHASE 3 (90-180 days): Medium severity gaps

For each phase list:
- Specific gaps to address
- Recommended approach
- Resource requirements
- Expected outcome

Write as professional prose with clear phase headings.
"""

GAP_NARRATIVE_PROMPT = """
Write a professional finding description for this
NIS2 compliance gap:

Gap Title: {title}
Category: {category}
Severity: {severity}
Current State: {current_state}
Required State: {required_state}
Business Impact: {business_impact}
NIS2 Article: {article_reference}

Write 2-3 sentences explaining:
1. What is currently missing or insufficient
2. What NIS2 requires (cite the article)
3. The business and regulatory risk

Professional tone. No bullet points. 100 words max.
"""

FINE_EXPOSURE_PROMPT = """
Calculate and explain the regulatory fine exposure
for this organisation:

Entity Type: {entity_type}
Annual Turnover: {annual_turnover}
Country: {country}
Critical Gaps: {critical_gaps}
Total Gaps: {total_gaps}

Explain:
1. Maximum fine under NIS2 for their entity type
2. Calculated maximum based on their size
3. Country-specific enforcement context in 2026
4. Personal liability risk for executives
5. Non-financial penalties (public disclosure,
   operating restrictions)

Be specific with euro amounts. Professional tone.
"""
```

### Acceptance criteria
- [ ] All prompts defined in claude_prompts.py
- [ ] Prompts use f-string compatible format vars
- [ ] System prompt defined separately
- [ ] File importable from generator.py

---

## TASK 10 — Report Generator: Charts Module

### What
Generate charts as images for embedding in PDF reports.
Use Plotly with kaleido for PNG export (both installed).

### File: report_generator/charts.py

```python
import plotly.graph_objects as go
import plotly.express as px
import io
import base64
from reportlab.lib.utils import ImageReader


def compliance_gauge_image(score: int,
                           sector_avg: int = None) -> bytes:
    """
    Generate compliance score gauge as PNG bytes.
    score: 0-100
    sector_avg: optional sector benchmark line
    """
    color = '#22c55e' if score >= 70 else \
            '#f59e0b' if score >= 40 else '#ef4444'

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Compliance Score",
               'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, 100],
                     'tickwidth': 1},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 40],
                 'color': '#fee2e2'},
                {'range': [40, 70],
                 'color': '#fef3c7'},
                {'range': [70, 100],
                 'color': '#dcfce7'},
            ],
            'threshold': {
                'line': {'color': '#1d4ed8',
                         'width': 4},
                'thickness': 0.75,
                'value': sector_avg or score
            }
        }
    ))
    fig.update_layout(
        width=500, height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='white',
    )
    return fig.to_image(format='png')


def severity_bar_chart_image(
        critical: int, high: int,
        medium: int, low: int) -> bytes:
    """
    Generate severity breakdown bar chart as PNG bytes.
    """
    fig = go.Figure(go.Bar(
        x=['Critical', 'High', 'Medium', 'Low'],
        y=[critical, high, medium, low],
        marker_color=['#dc2626', '#ea580c',
                      '#ca8a04', '#16a34a'],
        text=[critical, high, medium, low],
        textposition='outside',
    ))
    fig.update_layout(
        title='Gap Severity Distribution',
        width=600, height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        yaxis_title='Number of Gaps',
        showlegend=False,
    )
    return fig.to_image(format='png')


def category_heatmap_image(category_data: dict) -> bytes:
    """
    Generate category heatmap as PNG bytes.
    category_data: {'Access Control': 3, 'Incident Response': 5}
    """
    categories = list(category_data.keys())
    values = list(category_data.values())

    fig = go.Figure(go.Bar(
        x=values,
        y=categories,
        orientation='h',
        marker_color=[
            '#dc2626' if v >= 5 else
            '#ea580c' if v >= 3 else
            '#ca8a04' if v >= 1 else '#16a34a'
            for v in values
        ],
        text=values,
        textposition='outside',
    ))
    fig.update_layout(
        title='Gaps by NIS2 Category',
        width=700, height=400,
        margin=dict(l=150, r=50, t=50, b=20),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis_title='Number of Gaps',
    )
    return fig.to_image(format='png')


def remediation_timeline_image(phases: list) -> bytes:
    """
    Generate remediation timeline Gantt chart.
    phases: [{'name': 'Phase 1', 'start': 0,
               'end': 30, 'tasks': 5}]
    """
    fig = go.Figure()
    colors = ['#dc2626', '#ea580c', '#ca8a04']

    for i, phase in enumerate(phases):
        fig.add_trace(go.Bar(
            name=phase['name'],
            x=[phase['end'] - phase['start']],
            y=[phase['name']],
            base=[phase['start']],
            orientation='h',
            marker_color=colors[i],
            text=f"{phase['tasks']} gaps",
            textposition='inside',
        ))

    fig.update_layout(
        title='Remediation Timeline (Days)',
        width=700, height=300,
        barmode='stack',
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis_title='Days from Start',
        margin=dict(l=100, r=50, t=50, b=20),
    )
    return fig.to_image(format='png')


def png_to_reportlab_image(png_bytes: bytes,
                            width: float,
                            height: float):
    """Convert PNG bytes to ReportLab ImageReader."""
    return ImageReader(io.BytesIO(png_bytes))
```

### Acceptance criteria
- [ ] All four chart functions defined
- [ ] Each returns PNG bytes
- [ ] png_to_reportlab_image helper works
- [ ] Charts render without errors when tested
- [ ] Colors match dashboard color scheme

---

## TASK 11 — Report Generator: PDF Generator (Core)

### What
Core PDF generation using ReportLab.
Generates professional 20-30 page reports.
Two methods: sector report and gap analysis report.

### File: report_generator/generator.py

```python
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    getSampleStyleSheet, ParagraphStyle)
from reportlab.lib.units import cm
from reportlab.lib.colors import (
    HexColor, white, black)
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak,
    HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.graphics.shapes import Drawing
import anthropic

from .charts import (
    compliance_gauge_image,
    severity_bar_chart_image,
    category_heatmap_image,
    remediation_timeline_image,
    png_to_reportlab_image)
from .claude_prompts import (
    SECTOR_REPORT_SYSTEM,
    SECTOR_REQUIREMENTS_PROMPT,
    EXECUTIVE_SUMMARY_PROMPT,
    REMEDIATION_ROADMAP_PROMPT,
    GAP_NARRATIVE_PROMPT,
    FINE_EXPOSURE_PROMPT)


# Brand colors (AES AI Solutions)
BRAND_DARK = HexColor('#0f172a')
BRAND_BLUE = HexColor('#1d4ed8')
BRAND_LIGHT = HexColor('#f8fafc')
SEVERITY_CRITICAL = HexColor('#dc2626')
SEVERITY_HIGH = HexColor('#ea580c')
SEVERITY_MEDIUM = HexColor('#ca8a04')
SEVERITY_LOW = HexColor('#16a34a')


class NIS2ReportGenerator:

    def __init__(self):
        self.client = anthropic.Anthropic()
        self.styles = self._build_styles()

    def _build_styles(self):
        styles = getSampleStyleSheet()
        custom = {
            'ReportTitle': ParagraphStyle(
                'ReportTitle',
                fontSize=28,
                textColor=white,
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica-Bold',
            ),
            'ReportSubtitle': ParagraphStyle(
                'ReportSubtitle',
                fontSize=14,
                textColor=HexColor('#cbd5e1'),
                alignment=TA_CENTER,
                spaceAfter=8,
                fontName='Helvetica',
            ),
            'H1': ParagraphStyle(
                'H1',
                fontSize=20,
                textColor=BRAND_DARK,
                spaceBefore=20,
                spaceAfter=12,
                fontName='Helvetica-Bold',
            ),
            'H2': ParagraphStyle(
                'H2',
                fontSize=14,
                textColor=BRAND_BLUE,
                spaceBefore=16,
                spaceAfter=8,
                fontName='Helvetica-Bold',
            ),
            'Body': ParagraphStyle(
                'Body',
                fontSize=10,
                textColor=BRAND_DARK,
                spaceBefore=4,
                spaceAfter=6,
                leading=16,
                fontName='Helvetica',
            ),
            'Caption': ParagraphStyle(
                'Caption',
                fontSize=8,
                textColor=HexColor('#64748b'),
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName='Helvetica',
            ),
        }
        styles.add(custom['ReportTitle'])
        styles.add(custom['ReportSubtitle'])
        styles.add(custom['H1'])
        styles.add(custom['H2'])
        styles.add(custom['Body'])
        styles.add(custom['Caption'])
        return styles

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API and return text response."""
        message = self.client.messages.create(
            model='claude-sonnet-4-20250514',
            max_tokens=2000,
            system=SECTOR_REPORT_SYSTEM,
            messages=[{'role': 'user', 'content': prompt}]
        )
        return message.content[0].text

    def _cover_page(self, elements, report_type,
                    company_name, sector, date_str):
        """Build cover page with dark background."""
        # Dark cover table
        cover_data = [[
            Paragraph(
                'NIS2 COMPLIANCE REPORT',
                self.styles['ReportTitle']),
        ]]
        cover_table = Table(cover_data,
            colWidths=[18*cm])
        cover_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BRAND_DARK),
            ('TOPPADDING', (0,0), (-1,-1), 60),
            ('BOTTOMPADDING', (0,0), (-1,-1), 20),
        ]))
        elements.append(cover_table)

        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(
            report_type, self.styles['H1']))
        elements.append(Paragraph(
            company_name, self.styles['H2']))
        elements.append(Paragraph(
            f'Sector: {sector} | Date: {date_str}',
            self.styles['Body']))
        elements.append(Paragraph(
            'Prepared by AES AI Solutions | aes-ai.nl',
            self.styles['Caption']))
        elements.append(PageBreak())

    def generate_sector_report(
            self, company_name: str, sector: str,
            country: str, company_size: str,
            entity_type: str = 'IMPORTANT') -> bytes:
        """
        Generate Type 1: Sector Requirements Report.
        No documents needed. Returns PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        elements = []
        date_str = datetime.now().strftime('%B %Y')

        # Cover page
        self._cover_page(
            elements,
            'Sector Requirements Analysis',
            company_name, sector, date_str)

        # Table of contents header
        elements.append(Paragraph(
            'NIS2 Requirements for Your Organisation',
            self.styles['H1']))
        elements.append(HRFlowable(
            width='100%', thickness=1,
            color=BRAND_BLUE))
        elements.append(Spacer(1, 0.5*cm))

        # Generate main content via Claude
        prompt = SECTOR_REQUIREMENTS_PROMPT.format(
            company_name=company_name,
            sector=sector,
            country=country,
            entity_type=entity_type,
            company_size=company_size,
        )
        content = self._call_claude(prompt)

        # Render content paragraphs
        for paragraph in content.split('\n\n'):
            if paragraph.strip():
                if paragraph.startswith('#'):
                    clean = paragraph.lstrip('#').strip()
                    elements.append(Paragraph(
                        clean, self.styles['H2']))
                else:
                    elements.append(Paragraph(
                        paragraph.strip(),
                        self.styles['Body']))
                elements.append(Spacer(1, 0.3*cm))

        # Fine exposure section
        elements.append(PageBreak())
        elements.append(Paragraph(
            'Regulatory Fine Exposure',
            self.styles['H1']))
        fine_prompt = FINE_EXPOSURE_PROMPT.format(
            entity_type=entity_type,
            annual_turnover='Unknown',
            country=country,
            critical_gaps='N/A',
            total_gaps='N/A',
        )
        fine_content = self._call_claude(fine_prompt)
        elements.append(Paragraph(
            fine_content, self.styles['Body']))

        # CTA page
        elements.append(PageBreak())
        elements.append(Paragraph(
            'Next Steps', self.styles['H1']))
        elements.append(Paragraph(
            'This report outlines your NIS2 requirements. '
            'To understand your current compliance posture, '
            'upload your existing policies and procedures '
            'for a full gap analysis.',
            self.styles['Body']))

        doc.build(elements)
        return buffer.getvalue()

    def generate_gap_report(
            self, audit, gaps, client) -> bytes:
        """
        Generate Type 2: Gap Analysis Report.
        Full paid report from completed audit.
        Returns PDF bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        elements = []
        date_str = datetime.now().strftime('%B %Y')

        # Aggregate gap data
        gap_list = list(gaps)
        critical = sum(
            1 for g in gap_list
            if g.severity == 'CRITICAL')
        high = sum(
            1 for g in gap_list
            if g.severity == 'HIGH')
        medium = sum(
            1 for g in gap_list
            if g.severity == 'MEDIUM')
        low = sum(
            1 for g in gap_list
            if g.severity == 'LOW')
        total_hours = sum(
            g.estimated_hours or 0
            for g in gap_list)
        total_cost = sum(
            g.remediation_cost or 0
            for g in gap_list)

        # Category breakdown
        category_data = {}
        for gap in gap_list:
            cat = gap.category or 'Other'
            category_data[cat] = \
                category_data.get(cat, 0) + 1

        # Cover page
        self._cover_page(
            elements,
            'NIS2 Gap Analysis Report',
            client.company_name,
            client.sector, date_str)

        # Executive summary
        elements.append(Paragraph(
            'Executive Summary', self.styles['H1']))
        elements.append(HRFlowable(
            width='100%', thickness=1,
            color=BRAND_BLUE))
        elements.append(Spacer(1, 0.3*cm))

        top_gaps = '\n'.join([
            f'- {g.title} ({g.severity})'
            for g in gap_list[:5]
        ])
        exec_summary = self._call_claude(
            EXECUTIVE_SUMMARY_PROMPT.format(
                company_name=client.company_name,
                sector=client.sector,
                compliance_score=audit.compliance_score,
                total_gaps=len(gap_list),
                critical_gaps=critical,
                high_gaps=high,
                medium_gaps=medium,
                low_gaps=low,
                remediation_hours=total_hours,
                remediation_cost=total_cost,
                top_gaps_summary=top_gaps,
            ))
        elements.append(Paragraph(
            exec_summary, self.styles['Body']))

        # Compliance score gauge chart
        elements.append(PageBreak())
        elements.append(Paragraph(
            'Compliance Score', self.styles['H1']))
        gauge_png = compliance_gauge_image(
            audit.compliance_score)
        gauge_img = png_to_reportlab_image(
            gauge_png, 12*cm, 8*cm)
        elements.append(Image(
            gauge_img, width=12*cm, height=8*cm))
        elements.append(Paragraph(
            f'Overall NIS2 Compliance Score: '
            f'{audit.compliance_score}%',
            self.styles['Caption']))

        # Severity breakdown chart
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(
            'Gap Severity Distribution',
            self.styles['H2']))
        severity_png = severity_bar_chart_image(
            critical, high, medium, low)
        severity_img = png_to_reportlab_image(
            severity_png, 14*cm, 8*cm)
        elements.append(Image(
            severity_img, width=14*cm, height=8*cm))

        # Category heatmap
        elements.append(PageBreak())
        elements.append(Paragraph(
            'Gaps by Category', self.styles['H1']))
        heatmap_png = category_heatmap_image(
            category_data)
        heatmap_img = png_to_reportlab_image(
            heatmap_png, 15*cm, 9*cm)
        elements.append(Image(
            heatmap_img, width=15*cm, height=9*cm))

        # Gap detail table
        elements.append(PageBreak())
        elements.append(Paragraph(
            'Identified Compliance Gaps',
            self.styles['H1']))

        # Summary table
        gap_table_data = [
            ['#', 'Gap', 'Severity',
             'Category', 'Hours']
        ]
        severity_colors = {
            'CRITICAL': SEVERITY_CRITICAL,
            'HIGH': SEVERITY_HIGH,
            'MEDIUM': SEVERITY_MEDIUM,
            'LOW': SEVERITY_LOW,
        }
        for i, gap in enumerate(
                sorted(gap_list,
                    key=lambda g: ['CRITICAL',
                        'HIGH','MEDIUM','LOW'].index(
                        g.severity)), 1):
            gap_table_data.append([
                str(i),
                gap.title[:60],
                gap.severity,
                gap.category or 'Other',
                str(gap.estimated_hours or 0),
            ])

        gap_table = Table(
            gap_table_data,
            colWidths=[1*cm, 7*cm, 2.5*cm,
                       3.5*cm, 2*cm])
        gap_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0),
             BRAND_DARK),
            ('TEXTCOLOR', (0,0), (-1,0), white),
            ('FONTNAME', (0,0), (-1,0),
             'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1),
             [white, HexColor('#f8fafc')]),
            ('GRID', (0,0), (-1,-1), 0.5,
             HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(gap_table)

        # Individual gap details
        elements.append(PageBreak())
        elements.append(Paragraph(
            'Gap Analysis Detail', self.styles['H1']))

        for i, gap in enumerate(
                sorted(gap_list,
                    key=lambda g: ['CRITICAL',
                        'HIGH','MEDIUM','LOW'].index(
                        g.severity)), 1):
            sev_color = severity_colors.get(
                gap.severity, BRAND_DARK)
            elements.append(Paragraph(
                f'{i}. {gap.title}',
                self.styles['H2']))

            # Severity badge row
            badge_data = [[
                Paragraph(
                    f'Severity: {gap.severity}',
                    self.styles['Caption']),
                Paragraph(
                    f'Category: {gap.category}',
                    self.styles['Caption']),
                Paragraph(
                    f'Hours: {gap.estimated_hours}',
                    self.styles['Caption']),
            ]]
            badge_table = Table(
                badge_data,
                colWidths=[5*cm, 7*cm, 4*cm])
            badge_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,0),
                 sev_color),
                ('TEXTCOLOR', (0,0), (0,0), white),
                ('BACKGROUND', (1,0), (-1,-1),
                 HexColor('#f1f5f9')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING',
                 (0,0), (-1,-1), 4),
            ]))
            elements.append(badge_table)
            elements.append(Spacer(1, 0.3*cm))

            # Current vs Required state
            state_data = [[
                Paragraph(
                    'Current State',
                    self.styles['H2']),
                Paragraph(
                    'Required State',
                    self.styles['H2']),
            ],[
                Paragraph(
                    gap.current_state or 'Not assessed',
                    self.styles['Body']),
                Paragraph(
                    gap.required_state or '',
                    self.styles['Body']),
            ]]
            state_table = Table(
                state_data,
                colWidths=[8*cm, 8*cm])
            state_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,0),
                 HexColor('#fee2e2')),
                ('BACKGROUND', (1,0), (1,0),
                 HexColor('#dcfce7')),
                ('BACKGROUND', (0,1), (0,1),
                 HexColor('#fff5f5')),
                ('BACKGROUND', (1,1), (1,1),
                 HexColor('#f0fdf4')),
                ('GRID', (0,0), (-1,-1), 0.5,
                 HexColor('#e2e8f0')),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING',
                 (0,0), (-1,-1), 8),
                ('LEFTPADDING',
                 (0,0), (-1,-1), 8),
            ]))
            elements.append(state_table)

            if gap.business_impact:
                elements.append(Spacer(1, 0.2*cm))
                elements.append(Paragraph(
                    f'Business Impact: '
                    f'{gap.business_impact}',
                    self.styles['Body']))

            elements.append(Spacer(1, 0.5*cm))
            elements.append(HRFlowable(
                width='100%', thickness=0.5,
                color=HexColor('#e2e8f0')))
            elements.append(Spacer(1, 0.3*cm))

        # Remediation roadmap
        elements.append(PageBreak())
        elements.append(Paragraph(
            'Remediation Roadmap', self.styles['H1']))

        import json
        gaps_json = json.dumps([{
            'title': g.title,
            'severity': g.severity,
            'category': g.category,
            'estimated_hours': g.estimated_hours,
        } for g in gap_list[:20]], indent=2)

        roadmap = self._call_claude(
            REMEDIATION_ROADMAP_PROMPT.format(
                gaps_json=gaps_json,
                sector=client.sector,
                company_size=client.company_size,
                country=getattr(client, 'country', 'NL'),
            ))
        elements.append(Paragraph(
            roadmap, self.styles['Body']))

        # Roadmap timeline chart
        phases = [
            {'name': 'Phase 1 (0-30 days)',
             'start': 0, 'end': 30,
             'tasks': critical},
            {'name': 'Phase 2 (30-90 days)',
             'start': 30, 'end': 90,
             'tasks': high},
            {'name': 'Phase 3 (90-180 days)',
             'start': 90, 'end': 180,
             'tasks': medium},
        ]
        timeline_png = remediation_timeline_image(phases)
        timeline_img = png_to_reportlab_image(
            timeline_png, 15*cm, 7*cm)
        elements.append(Image(
            timeline_img, width=15*cm, height=7*cm))

        # Fine exposure
        elements.append(PageBreak())
        elements.append(Paragraph(
            'Regulatory Risk & Fine Exposure',
            self.styles['H1']))
        fine_content = self._call_claude(
            FINE_EXPOSURE_PROMPT.format(
                entity_type='IMPORTANT',
                annual_turnover='Unknown',
                country=getattr(client, 'country', 'NL'),
                critical_gaps=critical,
                total_gaps=len(gap_list),
            ))
        elements.append(Paragraph(
            fine_content, self.styles['Body']))

        # About AES page
        elements.append(PageBreak())
        elements.append(Paragraph(
            'About AES AI Solutions',
            self.styles['H1']))
        elements.append(Paragraph(
            'AES AI Solutions is a specialist NIS2 '
            'compliance technology firm based in the '
            'Netherlands. We combine AI-powered analysis '
            'with deep regulatory expertise to help '
            'organisations achieve and maintain NIS2 '
            'compliance. Contact us at support@aes-ai.nl',
            self.styles['Body']))

        doc.build(elements)
        return buffer.getvalue()
```

### Acceptance criteria
- [ ] generator.py importable without errors
- [ ] generate_sector_report() returns valid PDF bytes
- [ ] generate_gap_report() returns valid PDF bytes
- [ ] All charts embedded in PDF
- [ ] Claude generates content for each section
- [ ] Cover page renders with dark background
- [ ] Gap table renders with severity colors
- [ ] Current/Required state boxes render correctly

---

## TASK 12 — Report Generator: Views and URLs

### What
Wire report generation to Django views.
Two download endpoints + one sector report form page.

### File: report_generator/views.py

```python
import io
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (
    render, get_object_or_404, redirect)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.utils import timezone

from compliance_engine.models import (
    ComplianceAudit, ComplianceGap, Client)
from .generator import NIS2ReportGenerator


class SectorReportFormView(View):
    """
    Public-facing form: select sector and get
    a free sector requirements report PDF.
    Lead generation tool.
    """
    def get(self, request):
        from compliance_engine.models import Client
        sector_choices = Client.SECTOR_CHOICES
        country_choices = Client.COUNTRY_CHOICES
        return render(request,
            'report_generator/sector_report.html', {
            'sector_choices': sector_choices,
            'country_choices': country_choices,
        })

    def post(self, request):
        company_name = request.POST.get(
            'company_name', 'Your Organisation')
        sector = request.POST.get('sector', 'MSP')
        country = request.POST.get('country', 'NL')
        company_size = request.POST.get(
            'company_size', 'MEDIUM')
        entity_type = request.POST.get(
            'entity_type', 'IMPORTANT')
        email = request.POST.get('email', '')

        # TODO: Save lead to database
        # TODO: Send email with report attached

        generator = NIS2ReportGenerator()
        pdf_bytes = generator.generate_sector_report(
            company_name=company_name,
            sector=sector,
            country=country,
            company_size=company_size,
            entity_type=entity_type,
        )

        response = HttpResponse(
            pdf_bytes,
            content_type='application/pdf')
        filename = (
            f'NIS2-Sector-Report-{sector}-'
            f'{timezone.now().strftime("%Y%m%d")}.pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{filename}"')
        return response


class GapReportDownloadView(LoginRequiredMixin, View):
    """
    Download gap analysis PDF report for
    a completed audit. Sets report_generated=True.
    """
    def get(self, request, pk):
        audit = get_object_or_404(
            ComplianceAudit, pk=pk)
        client = audit.client
        gaps = ComplianceGap.objects.filter(
            audit=audit)

        if not gaps.exists():
            from django.contrib import messages
            messages.error(request,
                'Geen gaps gevonden voor dit audit')
            return redirect(
                'dashboard:audit_detail', pk=pk)

        generator = NIS2ReportGenerator()
        pdf_bytes = generator.generate_gap_report(
            audit=audit,
            gaps=gaps,
            client=client,
        )

        # Mark report as generated
        audit.report_generated = True
        audit.report_generated_at = timezone.now()
        audit.save(update_fields=[
            'report_generated',
            'report_generated_at'])

        response = HttpResponse(
            pdf_bytes,
            content_type='application/pdf')
        filename = (
            f'NIS2-Gap-Analysis-'
            f'{client.company_name.replace(" ", "-")}-'
            f'{timezone.now().strftime("%Y%m%d")}.pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{filename}"')
        return response


class GapReportGenerateView(LoginRequiredMixin, View):
    """
    HTMX endpoint: trigger report generation
    and return updated download button partial.
    """
    def post(self, request, pk):
        audit = get_object_or_404(
            ComplianceAudit, pk=pk)
        # Mark as generating (async in future)
        # For now generate synchronously
        return JsonResponse({
            'status': 'ready',
            'download_url': f'/reports/audit/{pk}/download/'
        })
```

### File: report_generator/urls.py

```python
from django.urls import path
from . import views

app_name = 'report_generator'

urlpatterns = [
    path('sector/',
        views.SectorReportFormView.as_view(),
        name='sector_report'),
    path('audit/<uuid:pk>/download/',
        views.GapReportDownloadView.as_view(),
        name='gap_report_download'),
    path('audit/<uuid:pk>/generate/',
        views.GapReportGenerateView.as_view(),
        name='gap_report_generate'),
]
```

### Wire download button in audit_detail.html
Find the "Rapport Downloaden" button and update href:
```html
<a href="{% url 'report_generator:gap_report_download' audit.pk %}"
   class="btn btn-primary"
   {% if not audit.compliance_score %}disabled{% endif %}>
  📄 Rapport Downloaden
</a>
```

Remove the `report_generated` gate — generate on demand.

### Acceptance criteria
- [ ] /reports/sector/ renders form
- [ ] Sector form POST returns PDF download
- [ ] /reports/audit/<pk>/download/ returns PDF
- [ ] report_generated set to True after download
- [ ] Download button in audit_detail.html works
- [ ] Filename includes company name and date
- [ ] 404 if audit not found
- [ ] Error message if no gaps exist

---

## TASK 13 — Sector Report Form Template

### What
Public-facing lead generation page.
Visitor fills in their details, downloads free report,
system captures their email as a lead.

### File: report_generator/templates/report_generator/sector_report.html

Template must include:
- Extend base template OR be standalone
- Hero section explaining the free report
- Form fields:
  - Company name (text input)
  - Email address (email input, required for lead capture)
  - Sector (select — use Client.SECTOR_CHOICES)
  - Country (select — use COUNTRY_CHOICES)
  - Company size (radio: Small/Medium/Large)
  - Entity type (radio: Essential Entity / Important Entity
    with tooltip explaining the difference)
- Submit button: "Genereer Gratis NIS2 Rapport"
- Loading state on submit (Alpine.js)
- What's included section (bullets):
  - Your NIS2 obligations by sector
  - Article 21 mandatory measures
  - Incident reporting requirements
  - Executive liability risks
  - Country-specific requirements
  - Regulatory fine exposure calculator
  - Recommended next steps
- Trust signals: "No signup required", "PDF download",
  "Based on official NIS2 Directive"
- CTA after form: "Need a full gap analysis?
  Upload your documents for €950"

### Acceptance criteria
- [ ] Form renders all fields
- [ ] Sector and country selects populated from choices
- [ ] Entity type has tooltip explanation
- [ ] Submit shows loading state
- [ ] Form POST triggers PDF download
- [ ] Page is professional and trustworthy
- [ ] Mobile responsive

---

## TASK 14 — Toast Notification System

### What
No feedback shown after POST actions (save client,
create audit, address gap, etc). Add Django messages
rendered as auto-dismissing toasts via Alpine.js.

### Files to modify
- dashboard/templates/dashboard/base.html
  (add toast container and Alpine.js component)

### Implementation
Add to base.html before closing </body>:

```html
<!-- Toast Notifications -->
{% if messages %}
<div
  x-data="{
    toasts: [
      {% for message in messages %}
      {
        id: {{ forloop.counter }},
        type: '{{ message.tags }}',
        text: '{{ message }}',
        visible: true
      }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ]
  }"
  class="fixed bottom-4 right-4 z-50
         flex flex-col gap-2"
>
  <template x-for="toast in toasts"
            :key="toast.id">
    <div
      x-show="toast.visible"
      x-init="setTimeout(() =>
        toast.visible = false, 4000)"
      x-transition:enter="transition ease-out duration-300"
      x-transition:enter-start="opacity-0 translate-y-2"
      x-transition:enter-end="opacity-100 translate-y-0"
      x-transition:leave="transition ease-in duration-200"
      x-transition:leave-end="opacity-0"
      :class="{
        'bg-green-600': toast.type === 'success',
        'bg-red-600': toast.type === 'error',
        'bg-blue-600': toast.type === 'info',
        'bg-yellow-600': toast.type === 'warning',
      }"
      class="text-white px-4 py-3 rounded-lg
             shadow-lg flex items-center gap-3
             min-w-64 max-w-sm"
    >
      <span x-text="toast.text"
            class="flex-1 text-sm"></span>
      <button
        @click="toast.visible = false"
        class="text-white/70 hover:text-white">
        ✕
      </button>
    </div>
  </template>
</div>
{% endif %}
```

### Acceptance criteria
- [ ] Success toasts show in green bottom-right
- [ ] Error toasts show in red
- [ ] Toasts auto-dismiss after 4 seconds
- [ ] Manual close button works
- [ ] Multiple toasts stack correctly
- [ ] Smooth enter/leave transitions
- [ ] Works on all dashboard pages

---

## TASK 15 — Loading States on Async Buttons

### What
"AI Analyse Starten" button has no loading state.
Users click multiple times thinking nothing happened.
Also fix all other async action buttons.

### Files to modify
- dashboard/templates/dashboard/audit_detail.html
  (AI Analyse Starten button)
- Any other buttons that trigger async operations

### Implementation pattern for AI Analyse button:

```html
<div x-data="{ running: false, error: null }">
  <button
    hx-post="{% url 'dashboard:audit_run' audit.pk %}"
    hx-indicator="#run-indicator"
    @htmx:before-request="running = true"
    @htmx:after-request="running = false"
    @htmx:response-error="
      running = false;
      error = 'Er is een fout opgetreden'"
    :disabled="running"
    :class="running ?
      'opacity-50 cursor-not-allowed' : ''"
    class="btn btn-primary flex items-center gap-2"
  >
    <span x-show="!running">🚀 AI Analyse Starten</span>
    <span x-show="running"
          class="flex items-center gap-2">
      <svg class="animate-spin h-4 w-4"
           xmlns="http://www.w3.org/2000/svg"
           fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12"
                r="10" stroke="currentColor"
                stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0
                 5.373 0 12h4z"></path>
      </svg>
      Analyseren...
    </span>
  </button>
  <p x-show="error" x-text="error"
     class="text-red-500 text-sm mt-2"></p>
</div>
```

### Apply same pattern to:
- Document upload button
- Audit transition buttons
- Gap mark-as-addressed submit
- Report generate button

### Acceptance criteria
- [ ] AI Analyse button shows spinner when running
- [ ] Button disabled during processing
- [ ] Error message shown if request fails
- [ ] All async buttons have loading states
- [ ] Spinner animation is smooth

---

## TASK 16 — Empty State CTAs

### What
New users see blank dashboard with no guidance.
Add helpful empty states with clear next actions.

### Files to modify
- dashboard/templates/dashboard/dashboard.html
- dashboard/templates/dashboard/clients.html
- dashboard/templates/dashboard/audits.html
- dashboard/templates/dashboard/gaps.html

### Empty state component pattern:

```html
{% if total_clients == 0 %}
<div class="flex flex-col items-center
            justify-center py-24 text-center">
  <div class="text-6xl mb-4">🛡️</div>
  <h3 class="text-xl font-semibold
              text-gray-900 mb-2">
    Welkom bij NIS2 Analyzer
  </h3>
  <p class="text-gray-500 mb-6 max-w-md">
    Voeg uw eerste klant toe om te beginnen
    met NIS2 compliance analyses.
  </p>
  <a href="{% url 'dashboard:client_new' %}"
     class="btn btn-primary">
    + Eerste Klant Toevoegen
  </a>
</div>
{% endif %}
```

### Empty states needed:
- dashboard.html: no clients → onboarding CTA
- clients.html: no clients → add first client
- audits.html: no audits → create first audit
- gaps.html: no gaps → run an audit first

### Acceptance criteria
- [ ] Dashboard shows onboarding CTA when no clients
- [ ] Clients page has empty state with add CTA
- [ ] Audits page has empty state with create CTA
- [ ] Gaps page explains to run an audit first
- [ ] Empty states styled consistently
- [ ] Empty states disappear when data exists

---

## TASK 17 — Fix report_generated Pipeline Hook

### What
After AI analysis completes, report_generated
is never set to True so download button never appears.
Fix the pipeline to set the flag correctly.

### Files to modify
- compliance_engine/views.py OR
  nis2_agents/orchestrator.py
  (wherever _run_nis2_pipeline is defined)

### Fix
After gaps are saved and audit score is calculated,
add:

```python
# After saving all gaps and updating compliance score
audit.report_generated = True
audit.report_generated_at = timezone.now()
audit.save(update_fields=[
    'status',
    'compliance_score',
    'report_generated',
    'report_generated_at',
    'completed_at',
])
```

### Also update audit_detail.html download button
Remove hard gate on report_generated.
Instead show button whenever audit has gaps:

```html
{% if gaps.count > 0 %}
<a href="{% url 'report_generator:gap_report_download'
          audit.pk %}"
   class="btn btn-primary">
  📄 Rapport Downloaden
</a>
{% elif audit.status == 'COMPLETE' %}
<p class="text-gray-500 text-sm">
  Rapport wordt gegenereerd...
</p>
{% endif %}
```

### Acceptance criteria
- [ ] report_generated=True after pipeline completes
- [ ] Download button appears after audit completes
- [ ] report_generated_at timestamp set correctly
- [ ] Existing completed audits can still download

---

## TASK 18 — Sidebar Navigation Update

### What
Add Reports section to sidebar navigation.
Add link to free sector report generator.

### Files to modify
- dashboard/templates/dashboard/base.html
  (sidebar nav section)

### Add to sidebar:
```html
<!-- Reports section -->
<li class="nav-section-label">
  Rapporten
</li>
<li>
  <a href="{% url 'report_generator:sector_report' %}"
     class="nav-link {% if 'sector_report'
       in request.resolver_match.url_name %}
       active{% endif %}">
    📊 Sector Rapport
  </a>
</li>
<li>
  <a href="{% url 'dashboard:audits' %}"
     class="nav-link">
    📄 Audit Rapporten
  </a>
</li>
```

### Acceptance criteria
- [ ] Reports section visible in sidebar
- [ ] Sector Report link goes to form page
- [ ] Active state works on sector report page
- [ ] Consistent styling with existing nav items

---

## FINAL CHECKLIST — Run After All Tasks Complete

```bash
# 1. Apply all migrations
python manage.py makemigrations
python manage.py migrate

# 2. Collect static files
python manage.py collectstatic --noinput

# 3. Run tests
python manage.py test

# 4. Test sector report generation manually
# Visit /reports/sector/ and generate a PDF

# 5. Test gap report download
# Complete an audit and click download

# 6. Verify all sidebar links work

# 7. Test empty states by clearing test data

# 8. Test toast notifications on all POST actions

# 9. Verify audit creation flow end-to-end:
#    Create client → Create audit → Upload doc
#    → Run analysis → Download report

# 10. Check no 404s in URL routing
python manage.py show_urls | grep dashboard
python manage.py show_urls | grep reports
```

---

## NOTES FOR CLAUDE CODE

- Keep all Dutch language strings consistent
- Do not use React or Vue — Alpine.js + HTMX only
- All new views must have LoginRequiredMixin
  except SectorReportFormView (public)
- Use UUID primary keys (existing pattern)
- Follow existing template styling patterns
- Run migrations after every model change
- Test each task before starting the next one
- If a file already exists, read it first
  before modifying
- ReportLab and Plotly are already installed
- Anthropic client uses existing ANTHROPIC_API_KEY
  from .env
```
