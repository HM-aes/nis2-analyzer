# 🛡️ NIS2 Compliance Analyzer

**Professional Django-based NIS2 Directive compliance consulting platform for Dutch IT companies**

## 🎯 Overview

This platform automates NIS2 compliance gap analysis using:
- **Django 6.0** - Web framework
- **Qdrant** - Vector database for NIS2 knowledge base
- **Pydantic AI + Claude** - Structured gap analysis
- **SQLite** - Client & audit database

## 🏗️ Architecture

### Core Components

1. **compliance_engine** - Main Django app
   - Models: Client, ComplianceAudit, ComplianceGap, ClientDocument
   - REST API for managing audits
   - Document upload and processing

2. **nis2_agents** - AI Agent System
   - **Auditor** - Gap analysis with Claude (Pydantic AI)
   - **Orchestrator** - Workflow coordination

3. **rag_engine** - Vector Database
   - Qdrant client for NIS2 knowledge base
   - Semantic search for requirements

## 🚀 Quick Start

### Prerequisites

- Python 3.12+

- Anthropic API key (Claude)

### Installation

```bash
# 1. Clone/extract the project
cd nis2-analyzer-complete

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# 6. Run Django migrations
python manage.py migrate

# 7. Create superuser
python manage.py createsuperuser

# 8. Start development server
python manage.py runserver
```

### Access the Application

- **Django Admin**: http://localhost:8000/admin
- **REST API**: http://localhost:8000/api/
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## 📊 Usage Workflow

### 1. Create a Client

```python
# Via Django admin or API
POST /api/clients/
{
  "company_name": "Example MSP BV",
  "kvk_number": "12345678",
  "sector": "MSP",
  "company_size": "MEDIUM",
  "contact_person": "Jan de Vries",
  "email": "jan@example.nl"
}
```

### 2. Create an Audit

```python
POST /api/audits/
{
  "client": "<client_uuid>",
  "tier": "T1",
  "quoted_price": 950.00
}
```

### 3. Upload Client Documents

```python
POST /api/documents/
Content-Type: multipart/form-data

{
  "audit": "<audit_uuid>",
  "document_type": "POLICY",
  "file": <security_policy.pdf>
}
```

### 4. Start AI Processing

```python
POST /api/audits/<audit_uuid>/start_processing/

# Returns:
{
  "message": "Processing started",
  "audit_id": "...",
  "status": "success"
}
```

### 5. View Results

```python
GET /api/gaps/?audit_id=<audit_uuid>

# Returns list of identified compliance gaps
```

## 🧠 AI Agent System

### Auditor Agent

Uses **Pydantic AI** with **Claude Sonnet 4** for structured gap analysis:

```python
from nis2_agents.auditor import NIS2Auditor

auditor = NIS2Auditor()
analysis = auditor.analyze_compliance_sync(
    client_documents="...",
    nis2_requirements=[...]
)

# Returns structured GapAnalysisOutput with:
# - List of ComplianceGap objects
# - Overall compliance score
# - Executive summary
# - Critical priorities
```

### Orchestrator

Coordinates the entire workflow:

```python
from nis2_agents.orchestrator import NIS2Orchestrator

orchestrator = NIS2Orchestrator()
result = orchestrator.process_audit(audit_id)

# Handles:
# 1. Document text extraction
# 2. RAG retrieval from Qdrant
# 3. AI gap analysis
# 4. Database storage
# 5. Report generation
```

## 🗄️ Qdrant Knowledge Base

### Populate with NIS2 Documents

```python
from rag_engine.qdrant_client import NIS2QdrantClient

qdrant = NIS2QdrantClient()

# Add a document chunk
qdrant.add_document(
    text="Article 21.2: Essential entities shall...",
    metadata={
        'source': 'NIS2_DIRECTIVE',
        'article': '21.2',
        'language': 'en',
        'authority_level': 10
    }
)

# Search for requirements
results = qdrant.search(
    query="incident response requirements",
    top_k=5,
    filters={'language': 'en'}
)
```

### Ingest Full NIS2 Corpus

```bash
python manage.py ingest_nis2_docs \
  --docs-dir sample_docs/NIS2-EU-documents \
  --language en \
  --clear
```

## 💰 Business Model

### Pricing Tiers

| Tier | Service | Price | Deliverable |
|------|---------|-------|-------------|
| T1 | Gap Analysis | €950 | 30-page PDF report |
| T2 | Implementation Docs | €2,500 | T1 + Policy templates |
| T3 | Full Package | €5,000 | T2 + Consultation |

### Revenue Calculation

```python
# Conservative: 4 audits/month
# 3x T1 (€950) + 1x T2 (€2,500) = €5,350/month
# Annual: €64,200

# Realistic: 8 audits/month
# 5x T1 + 2x T2 + 1x T3 = €14,750/month
# Annual: €177,000
```

## 🔐 Security Features

- PII detection (Presidio - planned)
- Virus scanning (ClamAV - planned)
- Data encryption at rest
- Secure file uploads
- GDPR compliant data handling

## 📦 Database Models

### Client
Company information, sector, contact details

### ComplianceAudit
Tracks audit status, pricing, timeline, compliance score

### ComplianceGap
Individual NIS2 gaps with severity, recommendations, effort estimates

### ClientDocument
Uploaded documents with processing status

### KnowledgeDocument
NIS2 corpus tracking (what's in Qdrant)

## 🛠️ Development

### Run Tests

```bash
python manage.py test
```

### Create Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Django Shell

```bash
python manage.py shell

# Test components
from compliance_engine.models import Client
from nis2_agents.auditor import NIS2Auditor
from rag_engine.qdrant_client import NIS2QdrantClient
```

## 🚢 Deployment

```bash
# Set DEBUG=False and configure ALLOWED_HOSTS in .env
python manage.py collectstatic
python manage.py runserver 0.0.0.0:8000
```

## 📝 TODO / Roadmap

### Phase 1 (MVP) ✅
- [x] Django models and admin
- [x] REST API
- [x] Qdrant integration
- [x] Pydantic AI Auditor
- [x] Basic orchestration

### Phase 2
- [ ] PDF report generation (ReportLab)
- [ ] Security Gatekeeper agent (virus scan, PII)
- [ ] Intelligence Analyst agent (charts/visualizations)
- [ ] Complete ingestion script
- [ ] Document text extraction (pdfplumber, python-docx)

### Phase 3
- [ ] Frontend dashboard (React/Vue)
- [ ] Client portal
- [ ] Email notifications
- [ ] Stripe payment integration

## 🤝 Support

For questions or issues:
- Email: support@aes-ai.nl
- GitHub Issues: [repository]

## 📄 License

Proprietary - AES AI Solutions
© 2026 All Rights Reserved

---

**Built with ❤️ for Dutch IT security**
