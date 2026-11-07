# Backend Testing Guide — NIS2 Analyzer

**Purpose:** Everything needed to run and test the backend end‑to‑end on a local
machine. Supersedes the older `RAG_TESTING_GUIDE.md` (which referenced paths,
a management command, and an Anthropic‑based auditor that no longer match the code).

_Last updated: 2026-09-08_

---

## 1. What the backend actually is

| Layer | Implementation | Notes |
|-------|----------------|-------|
| Web framework | Django 6 + DRF | `nis2_analyzer/` project, apps below |
| DB (local) | **SQLite** (`db.sqlite3`) | Postgres only needed on Railway |
| Vector DB (local) | **Qdrant on‑disk** (`qdrant_local/`) | No server, no API key needed locally |
| Embeddings | `fastembed` → `BAAI/bge-small-en-v1.5` (384‑dim) | Model auto‑downloads on first use (~90 MB) |
| Gap‑analysis LLM | **Google Gemini** (`gemini-2.0-flash-lite`) via Pydantic AI | Needs `GOOGLE_API_KEY` |
| PDF report LLM | **Anthropic Claude** (`report_generator/generator.py`) | Needs `ANTHROPIC_API_KEY` |
| Document text extraction | Docling if installed, else pdfplumber / python‑docx fallback | Fallback added so testing works without Docling |

Two pipelines call the same `nis2_agents.auditor.NIS2Auditor`:

- **Dashboard** — `POST /dashboard/audits/<pk>/run/` → `dashboard/views.py::_run_nis2_pipeline`
  (background thread, no language filter on RAG).
- **REST API** — `POST /api/audits/<uuid>/start_processing/` → `nis2_agents/orchestrator.py`
  (synchronous, also generates a ReportLab PDF).

---

## 2. Readiness status (2026-09-08)

| Item | Status | Action |
|------|--------|--------|
| `python manage.py check` | ✅ passes | — |
| Migrations applied | ✅ | `db.sqlite3` present, superuser `admin` exists |
| Test suite (`manage.py test`) | ✅ 64 pass | Does **not** exercise the live LLM pipeline |
| `nis2_agents/auditor.py` imports | ✅ **fixed** | Was importing removed `pydantic_ai.models.gemini` / `providers.google_gla`; now `models.google.GoogleModel` + `providers.google.GoogleProvider` |
| `orchestrator.py` RAG language filter | ✅ **fixed** | Was `language='nl'` (KB is `'en'`) → always 0 requirements; now `'en'` |
| `ingest_nis2_docs` management command | ✅ **added** | `compliance_engine/management/commands/ingest_nis2_docs.py`, with pdfplumber fallback + skips the `(1)` duplicate PDF |
| Document extraction without Docling | ✅ **fixed** | `DocumentProcessor` now falls back to pdfplumber / python‑docx / plain text |
| `rag_engine/qdrant_client.py` search | ✅ **fixed** | qdrant-client 1.19 removed `.search()`; now uses `.query_points()` |
| Qdrant knowledge base populated | ✅ **done** | 620 chunks ingested from the 2 NIS2 PDFs; RAG search verified |
| Pipeline dry‑run (extraction → RAG → gap save, LLM stubbed) | ✅ verified | `orchestrator.process_audit()` reaches `COMPLETE`; only the live Gemini call needs a real key |
| `GOOGLE_API_KEY` in `.env` | ❌ placeholder | Required for any gap analysis — see Step 2 |
| `ANTHROPIC_API_KEY` in `.env` | ❌ placeholder | Required for PDF report generation only |
| `docling` package | ➖ not installed | Optional; fallback covers PDF/DOCX/TXT. `pip install docling` for best extraction |
| Postgres / Qdrant Cloud keys | ➖ not needed locally | Production (Railway) only |

---

## 3. Setup steps

### Step 1 — Environment

```bash
cd /Users/hm/Documents/NIS2-Analyzer-complete/nis2-analyzer
source venv/bin/activate            # Python 3.11, deps already installed
python manage.py check
python manage.py migrate            # already applied; safe to re-run
python manage.py createsuperuser    # skip — 'admin' already exists
```

### Step 2 — API keys (`.env`)

Only these two matter for backend testing. Edit `.env`:

```
GOOGLE_API_KEY=<real key>       # https://aistudio.google.com/apikey  (free tier is enough)
ANTHROPIC_API_KEY=<real key>    # only needed to generate PDF reports
```

Leave `DATABASE_URL` empty (→ SQLite) and `QDRANT_HOST/PORT` as‑is (→ on‑disk Qdrant).
`GOOGLE_CLIENT_ID/SECRET` are for Google OAuth login only — not required for API/shell testing.

### Step 3 — Populate the NIS2 knowledge base (one time)

```bash
python manage.py ingest_nis2_docs --clear
```

- Reads PDFs from `NIS2-EU-documents/` (skips the `… (1).pdf` duplicate).
- First run downloads the `bge-small-en-v1.5` embedding model.
- Expect a few hundred to a couple thousand chunks.

Verify:

```bash
python manage.py shell -c "
from rag_engine.qdrant_client import NIS2QdrantClient
q = NIS2QdrantClient()
print('points:', q.get_collection_info().points_count)
for r in q.search('incident reporting obligations', top_k=3):
    print(round(r['score'],3), r['text'][:80])
"
```

Ready when: `points` > 200 and searches return NIS2 text with sensible scores.

---

## 4. End‑to‑end test (Django shell)

```bash
python manage.py shell
```

```python
from decimal import Decimal
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from compliance_engine.models import Client, ComplianceAudit, ComplianceGap, ClientDocument
from nis2_agents.orchestrator import NIS2Orchestrator

user = User.objects.get(username="admin")
client = Client.objects.create(
    company_name="Test MSP BV", kvk_number="99887766", sector="MSP",
    company_size="MEDIUM", contact_person="Jan de Vries", email="jan@test.nl",
    address="Teststraat 1", city="Amsterdam", postal_code="1011AA",
    account_manager=user,
)
audit = ComplianceAudit.objects.create(
    client=client, tier="T1", quoted_price=Decimal("950"), status="INTAKE",
)

sample = b"""SECURITY POLICY TEST MSP BV
1. ACCESS CONTROL: username + password only, no MFA. Shared admin accounts.
2. INCIDENT RESPONSE: no formal plan, ad-hoc via email, no SIEM/log monitoring.
3. SUPPLY CHAIN: 15+ vendors, no contractual security requirements.
4. NETWORK: firewall present, no segmentation, no IDS.
5. ENCRYPTION: data at rest and backups not encrypted.
6. TRAINING: no annual security awareness training, no phishing simulations.
"""
doc = ClientDocument.objects.create(
    audit=audit, document_type="POLICY",
    file=ContentFile(sample, name="security_policy.txt"),
    original_filename="security_policy.txt", file_size_bytes=len(sample),
    processed=True, uploaded_by=user,
)

result = NIS2Orchestrator().process_audit(str(audit.id))
print(result)

audit.refresh_from_db()
print("status:", audit.status, "score:", audit.compliance_score, "gaps:", audit.gaps_identified)
for g in ComplianceGap.objects.filter(audit=audit):
    print(f"[{g.severity}] {g.title} — {g.nis2_article}")
```

**Pass criteria**

- [ ] `result["status"] == "success"`
- [ ] `audit.status == "COMPLETE"` (orchestrator) — dashboard pipeline leaves it at `REVIEW`
- [ ] 5–15 gaps, each with a real `nis2_article` (e.g. `Article 21`, `Article 23`)
- [ ] `compliance_score` between ~10 and ~90 (not always 0 / 100)
- [ ] PDF written under `media/reports/` (needs `ANTHROPIC_API_KEY` for narrative sections)

---

## 5. REST API testing

Auth: DRF is configured with **SessionAuthentication + IsAuthenticated only**
(no token/basic auth). So either:

- Log in at `/admin/` or `/login/` in a browser, then use the browsable API at `/api/`, **or**
- Use a `requests.Session`, POST to the login page to get the `sessionid` cookie, then call `/api/…`.

Key endpoints:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/api/clients/` | Client CRUD |
| GET/POST | `/api/audits/` | Audit CRUD |
| POST | `/api/audits/{uuid}/start_processing/` | Run analysis (audit must be `INTAKE`) |
| GET | `/api/audits/{uuid}/download_report/` | Download PDF (after report generated) |
| GET | `/api/gaps/?audit_id={uuid}` | Gaps for an audit |
| POST | `/api/documents/{uuid}/process/` | Security gatekeeper (Presidio PII scan) |

---

## 6. Dashboard testing (browser)

```bash
python manage.py runserver
```

1. Log in at `http://localhost:8000/login/` (`admin`).
2. `http://localhost:8000/dashboard/` → create client → create audit.
3. Open the audit → **Documents** tab → upload a `.txt`/`.pdf`/`.docx`.
4. Click **Run AI analysis**. Status polls INTAKE → PROCESSING → ANALYSIS → REVIEW via HTMX.
5. When gaps exist, **Download gap report** (`/reports/audit/<pk>/download/`) — needs `ANTHROPIC_API_KEY`.
6. Public lead‑gen report: `http://localhost:8000/reports/` (also needs `ANTHROPIC_API_KEY`).

---

## 7. Known gaps / not blockers for local testing

- **Docling not installed** — extraction falls back to pdfplumber/python‑docx; scanned/image PDFs will extract poorly. `pip install docling` to improve.
- **`security_gatekeeper.py` (Presidio)** — first run downloads spaCy models; ClamAV virus scan is a stub.
- **No automated tests** cover the live Gemini/Claude calls — they cost tokens and need keys.
- **Postgres + Qdrant Cloud + `QDRANT_API_KEY`** — only for Railway deploy; ignore for local testing.
