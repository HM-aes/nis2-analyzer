# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django-based SaaS platform for automated NIS2 (Network and Information Security Directive) compliance gap analysis for Dutch IT companies. The system uses Claude (via Pydantic AI) to analyze uploaded client documents against NIS2 requirements stored in a Qdrant vector database.

## Development Commands

```bash
# Setup
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then set ANTHROPIC_API_KEY and DATABASE_URL
docker-compose up -d          # starts PostgreSQL and Qdrant
python manage.py migrate
python manage.py runserver

# Tests
python manage.py test                              # all tests
python manage.py test compliance_engine            # single app
python manage.py test compliance_engine.tests.TestName  # single test

# Database
python manage.py makemigrations
python manage.py migrate
python manage.py shell                             # Django REPL
```

## Architecture

### Apps

- **`compliance_engine/`** — Core Django app: models, REST API (DRF ViewSets), serializers, admin
- **`nis2_agents/`** — AI agent system using Pydantic AI + Claude Sonnet 4
- **`rag_engine/`** — Qdrant vector DB wrapper for semantic search over NIS2 knowledge base
- **`nis2_analyzer/`** — Django project config (settings, root URLs, WSGI)

### Data Flow

```
POST /api/audits/{id}/start_processing/
  → orchestrator.py: extract document text → Qdrant semantic search (top 20)
  → auditor.py: Claude analyzes gaps against NIS2 requirements
  → ComplianceGap records saved → ComplianceAudit status/score updated
```

### Key Models (`compliance_engine/models.py`)

- **Client** — Dutch company with KVK number, sector, and size tier
- **ComplianceAudit** — Audit lifecycle (INTAKE → PROCESSING → ANALYSIS → REVIEW → COMPLETE → DELIVERED); stores compliance score and report
- **ComplianceGap** — Individual gap with severity (CRITICAL/HIGH/MEDIUM/LOW), NIS2 article reference, current vs. required state, remediation effort
- **ClientDocument** — Uploaded files (PDF/DOCX/TXT/MD, max 50MB); tracks virus scan and PII detection status
- **KnowledgeDocument** — Tracks NIS2 knowledge base documents ingested into Qdrant

### AI Agent System (`nis2_agents/`)

- **`auditor.py`** — Pydantic AI agent using `claude-sonnet-4-20250514`; produces structured `GapAnalysisOutput` (gaps list, 0–100 compliance score, executive summary, top 3 priorities)
- **`orchestrator.py`** — Coordinates the 5-step workflow; marks audit as manual review on failure

### RAG Engine (`rag_engine/qdrant_client.py`)

- Qdrant collection `nis2_knowledge_base` with 384-dim COSINE vectors
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Methods: `add_document(text, metadata)`, `search(query, top_k, filters)`

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/api/clients/` | Client CRUD |
| GET/POST | `/api/audits/` | Audit CRUD |
| POST | `/api/audits/{id}/start_processing/` | Trigger AI analysis |
| GET | `/api/audits/{id}/download_report/` | Download PDF report |
| GET | `/api/gaps/?audit_id={uuid}` | Retrieve gaps for an audit |
| POST | `/api/documents/{id}/process/` | Run security gatekeeper |

### Infrastructure

- **PostgreSQL 16** — Application data (docker-compose port 5432)
- **Qdrant** — Vector DB (docker-compose ports 6333 HTTP, 6334 gRPC)
- **Locale:** Dutch (nl-NL), Timezone: Europe/Amsterdam

### Environment Variables

Key variables from `.env` (see `.env.example`):
- `ANTHROPIC_API_KEY` — Required for Claude
- `DATABASE_URL` — PostgreSQL connection string
- `QDRANT_HOST` / `QDRANT_PORT` — Vector DB connection
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`

## Implementation Status

Phase 1 (complete): Models, REST API, Qdrant integration, Pydantic AI auditor, orchestration, document upload.

Phase 2 (planned): PDF report generation (ReportLab), Security Gatekeeper agent (PII/virus), Intelligence Analyst agent (Plotly visualizations), document text extraction.

Phase 3 (planned): React/Vue frontend, client portal, Stripe payments.
