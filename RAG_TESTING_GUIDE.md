# Deployment Readiness Guide — NIS2 Analyzer

> **Doel:** Wat moet er nog gedaan worden voordat de applicatie live kan? Dit document beschrijft de stappen in volgorde.

---

## Status Overzicht

| Onderdeel | Status | Actie vereist |
|-----------|--------|---------------|
| Django backend + REST API | ✅ Compleet | — |
| Login pagina (dark mode UI) | ✅ Compleet | — |
| Dashboard UI | ✅ Compleet | — |
| Pydantic AI auditor agent | ✅ Compleet | — |
| Qdrant vector DB opzetten | ⚠️ Vereist | Zie Stap 1 |
| NIS2 kennisbank ingesteren | ⚠️ Vereist | Zie Stap 2 |
| Language filter fix | ⚠️ Vereist | Zie Stap 3 |
| Text extractie (PDF/TXT) | ⚠️ Vereist | Zie Stap 4 |
| End-to-end test | ⚠️ Vereist | Zie Stap 5 |
| PDF rapport generatie | 🔜 Phase 2 | — |
| React frontend | 🔜 Phase 3 | — |

---

## Stap 1 — Services opstarten

```bash
cd /Users/hm/Documents/nis2-analyzer-complete
source venv/bin/activate

# Kopieer env als nog niet gedaan
cp .env.example .env
# Stel in: ANTHROPIC_API_KEY

# Migraties
python manage.py migrate

# Superuser aanmaken (voor dashboard login)
python manage.py createsuperuser

# Server starten
python manage.py runserver
# → http://localhost:8000/dashboard/
```

**Verifieer Qdrant draait:**
```bash
curl http://localhost:6333/health
# {"title":"qdrant - vector search engine"}
```

---

## Stap 2 — NIS2 kennisbank ingesteren in Qdrant

De Qdrant collectie is momenteel leeg. Zonder dit heeft Claude geen NIS2-context om tegen te vergelijken.

### 2.1 Maak de management command directory

```bash
mkdir -p compliance_engine/management/commands
touch compliance_engine/management/__init__.py
touch compliance_engine/management/commands/__init__.py
```

### 2.2 Maak `compliance_engine/management/commands/ingest_nis2_docs.py`

```python
"""
python manage.py ingest_nis2_docs
"""
import os
import re
from django.core.management.base import BaseCommand
from rag_engine.qdrant_client import NIS2QdrantClient

class Command(BaseCommand):
    help = 'Ingesteer NIS2 PDF documenten in Qdrant vector database'

    def add_arguments(self, parser):
        parser.add_argument('--docs-dir', default='sample_docs/NIS2-EU-documents')
        parser.add_argument('--chunk-size', type=int, default=500)
        parser.add_argument('--overlap', type=int, default=100)
        parser.add_argument('--language', default='en')
        parser.add_argument('--clear', action='store_true')

    def handle(self, *args, **options):
        import pdfplumber

        qdrant = NIS2QdrantClient()

        if options['clear']:
            self.stdout.write("Verwijder bestaande collectie...")
            qdrant.delete_collection()
            qdrant._ensure_collection()

        docs_dir = options['docs_dir']
        pdf_files = [f for f in os.listdir(docs_dir) if f.endswith('.pdf')]
        self.stdout.write(f"Gevonden {len(pdf_files)} PDF bestanden")

        total_chunks = 0

        for pdf_file in pdf_files:
            if '(1)' in pdf_file:
                continue  # skip duplicates

            pdf_path = os.path.join(docs_dir, pdf_file)
            self.stdout.write(f"Verwerk: {pdf_file}")

            try:
                with pdfplumber.open(pdf_path) as pdf:
                    full_text = ""
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"

                chunks = self._chunk_text(full_text, options['chunk_size'], options['overlap'])

                for i, chunk in enumerate(chunks):
                    if len(chunk.strip()) < 50:
                        continue

                    article_ref = self._detect_article(chunk)
                    qdrant.add_document(
                        text=chunk,
                        metadata={
                            'source': 'NIS2_DIRECTIVE',
                            'language': options['language'],
                            'file': pdf_file,
                            'chunk_index': i,
                            'article': article_ref or f"chunk_{i}",
                            'title': f"NIS2 - {pdf_file} - chunk {i}",
                        }
                    )
                    total_chunks += 1

                    if i % 50 == 0:
                        self.stdout.write(f"  {i}/{len(chunks)} chunks...")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Fout bij {pdf_file}: {e}"))

        info = qdrant.get_collection_info()
        self.stdout.write(self.style.SUCCESS(
            f"\n✓ Klaar: {total_chunks} chunks — Qdrant: {info.vectors_count} vectoren"
        ))

    def _chunk_text(self, text, chunk_size, overlap):
        chunks, start = [], 0
        while start < len(text):
            chunks.append(text[start:start + chunk_size])
            start += chunk_size - overlap
        return chunks

    def _detect_article(self, text):
        for pattern in [r'Article\s+(\d+(?:\.\d+)?)', r'Art\.\s+(\d+(?:\.\d+)?)', r'Artikel\s+(\d+(?:\.\d+)?)']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"Article {match.group(1)}"
        return None
```

### 2.3 Voer ingestie uit

```bash
python manage.py ingest_nis2_docs \
    --docs-dir sample_docs/NIS2-EU-documents \
    --chunk-size 500 \
    --overlap 100 \
    --language en \
    --clear

# Verwacht: > 500 vectoren opgeslagen
```

### 2.4 Verifieer

```bash
python manage.py shell
```

```python
from rag_engine.qdrant_client import NIS2QdrantClient
qdrant = NIS2QdrantClient()

info = qdrant.get_collection_info()
print(f"Vectoren: {info.vectors_count}")   # moet > 500 zijn

results = qdrant.search("multi-factor authentication requirements", top_k=5)
for r in results:
    print(f"Score: {r['score']:.3f} | {r['text'][:80]}...")
```

---

## Stap 3 — Fix language filter in orchestrator

**Bestand:** `nis2_agents/orchestrator.py` (~regel 69)

De PDFs zijn Engels (`language='en'`) maar de orchestrator zoekt op `language='nl'` → altijd 0 resultaten.

```python
# Verander dit:
nis2_context = self.qdrant.search(
    query=search_query,
    top_k=20,
    filters={'language': 'nl'}
)

# Naar dit:
nis2_context = self.qdrant.search(
    query=search_query,
    top_k=20,
    filters={'language': 'en'}
)
```

---

## Stap 4 — Fix text extractie (placeholder vervangen)

**Bestand:** `nis2_agents/orchestrator.py`

De huidige `_extract_text` retourneert alleen de bestandsnaam. Claude analyseert hierdoor nooit echte client-documenten.

```python
def _extract_text(self, document: ClientDocument) -> str:
    """Extract text from uploaded document"""
    try:
        if document.original_filename.endswith('.txt'):
            with open(document.file.path, 'r', encoding='utf-8') as f:
                return f.read()
        elif document.original_filename.endswith('.pdf'):
            import pdfplumber
            with pdfplumber.open(document.file.path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        else:
            return f"[Kan tekst niet extraheren uit {document.original_filename}]"
    except Exception as e:
        logger.error(f"Text extractie fout: {e}")
        return f"[Extractie mislukt: {document.original_filename}]"
```

---

## Stap 5 — End-to-end test

### 5.1 Maak een testdocument

Sla op als `test_security_policy.txt`:

```
BEVEILIGINGSBELEID TEST MSP BV

1. TOEGANGSBEHEER
Wij gebruiken gebruikersnaam en wachtwoord. Geen MFA geïmplementeerd.
Admin accounts worden gedeeld tussen teamleden.

2. INCIDENT RESPONSE
Geen formeel incident response plan. Incidenten worden ad-hoc afgehandeld via email.
Geen SIEM of log monitoring.

3. SUPPLY CHAIN
15+ externe leveranciers zonder contractuele beveiligingsvereisten.

4. NETWERK BEVEILIGING
Firewall aanwezig. Geen netwerksegmentatie. Geen intrusion detection.

5. ENCRYPTIE
Data at rest niet versleuteld. Back-ups niet versleuteld.

6. TRAINING
Geen jaarlijkse security awareness training. Geen phishing simulaties.
```

### 5.2 Test via Django shell

```python
from compliance_engine.models import Client, ComplianceAudit, ClientDocument
from django.contrib.auth.models import User
from nis2_agents.orchestrator import NIS2Orchestrator

# Client + audit aanmaken
client = Client.objects.first()
audit = ComplianceAudit.objects.create(
    client=client, tier='T1', quoted_price=950, status='INTAKE'
)

# Document uploaden via dashboard of shell
# (zorg dat ClientDocument bestaat met processed=True)

# Start audit
orchestrator = NIS2Orchestrator()
result = orchestrator.process_audit(str(audit.id))
print(result)

# Verwacht:
# {'status': 'success', 'gaps_found': 8-15, 'compliance_score': 20-45}
```

### 5.3 Verificatie checklist

```python
from compliance_engine.models import ComplianceAudit, ComplianceGap

audit = ComplianceAudit.objects.latest('created_at')
print(f"Status: {audit.status}")          # moet COMPLETE zijn
print(f"Score:  {audit.compliance_score}%")
print(f"Gaps:   {audit.gaps_identified}")

gaps = ComplianceGap.objects.filter(audit=audit)
for gap in gaps:
    print(f"[{gap.severity}] {gap.title} | {gap.nis2_article}")
```

**Deployment ready als:**
- [ ] Qdrant heeft > 500 vectoren
- [ ] `status = COMPLETE` na verwerking
- [ ] Gaps bevatten echte NIS2 artikel nummers (Article 21, 23, etc.)
- [ ] Compliance score tussen 10–90 (niet altijd 0 of 100)
- [ ] Dashboard toont KPIs, gaps en score correct

---

## Beschikbare NIS2 documenten in `sample_docs/`

| Bestand | Inhoud | Prioriteit |
|---------|--------|------------|
| `CELEX_32022L2555_EN_TXT.pdf` | Volledige NIS2 Directive (artikelen 1-46) | ★★★ Ingesteren eerst |
| `OJ_L_202402690_EN_TXT.pdf` | Official Journal / implementing regulations | ★★ |
| `ENISA_Technical_Implementation_Guidance_Mapping_table_v1.2.xlsx` | ENISA mapping tabel | ★★ (requires pandas) |
| `CELEX_32022L2555_EN_TXT (1).pdf` | Duplicate | Skip |

---

*Laatste update: 2026-03-13*
