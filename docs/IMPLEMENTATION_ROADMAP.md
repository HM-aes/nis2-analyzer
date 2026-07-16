# 🚀 Implementation Roadmap - NIS2 Compliance Analyzer

## Current Status: Production-Ready MVP ✅

**What's Working:**
- ✅ Django models and admin interface
- ✅ REST API with Django REST Framework
- ✅ Pydantic AI integration with Claude
- ✅ Qdrant vector database for RAG
- ✅ Basic orchestration workflow
- ✅ Web dashboard

**What Needs Implementation:**
- ❌ Document text extraction (PDF, DOCX)
- ❌ PDF report generation
- ❌ Security Gatekeeper (virus scan, PII detection)
- ❌ Comprehensive test suite
- ❌ Async task processing (Celery)
- ❌ Caching layer (Redis)
- ❌ Production deployment configuration

---

## Phase 1: Core Feature Completion (Week 1-2)

### 1.1 Document Text Extraction

**Priority**: CRITICAL  
**Effort**: 8 hours  
**Files to Create/Modify**:
- `nis2_agents/document_processor.py` (new)
- `nis2_agents/orchestrator.py` (update)

**Implementation:**

```python
# nis2_agents/document_processor.py
"""
Document text extraction for multiple file formats
"""
import pdfplumber
from docx import Document
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Extract text from various document formats"""
    
    def extract_text(self, file_path: str, file_type: str) -> Optional[str]:
        """
        Extract text from document
        
        Args:
            file_path: Path to the document
            file_type: File extension (pdf, docx, txt)
        
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            if file_type.lower() == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type.lower() in ['docx', 'doc']:
                return self._extract_from_docx(file_path)
            elif file_type.lower() == 'txt':
                return self._extract_from_txt(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_type}")
                return None
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return None
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber"""
        text_parts = []
        
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX using python-docx"""
        doc = Document(file_path)
        text_parts = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        
        return "\n\n".join(text_parts)
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from plain text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_page_count(self, file_path: str, file_type: str) -> int:
        """Get number of pages in document"""
        try:
            if file_type.lower() == 'pdf':
                with pdfplumber.open(file_path) as pdf:
                    return len(pdf.pages)
            elif file_type.lower() in ['docx', 'doc']:
                # DOCX doesn't have clear page concept
                doc = Document(file_path)
                return len(doc.paragraphs) // 40  # Rough estimate
            else:
                return 1
        except Exception as e:
            logger.error(f"Error getting page count: {e}")
            return 0
```

**Update Orchestrator:**

```python
# In nis2_agents/orchestrator.py
from .document_processor import DocumentProcessor

class NIS2Orchestrator:
    def __init__(self):
        self.qdrant = NIS2QdrantClient()
        self.auditor = NIS2Auditor()
        self.doc_processor = DocumentProcessor()  # Add this
    
    def _extract_text(self, document: ClientDocument) -> str:
        """Extract text from a document"""
        file_extension = document.original_filename.split('.')[-1]
        text = self.doc_processor.extract_text(
            document.file.path,
            file_extension
        )
        
        if text:
            document.text_extracted = True
            document.pages_count = self.doc_processor.get_page_count(
                document.file.path,
                file_extension
            )
            document.processed = True
            document.processed_at = timezone.now()
            document.save()
        
        return text or f"[Failed to extract text from {document.original_filename}]"
```

**Testing:**
```python
# tests/test_document_processor.py
import pytest
from nis2_agents.document_processor import DocumentProcessor

def test_extract_pdf():
    processor = DocumentProcessor()
    text = processor.extract_text('sample_docs/test.pdf', 'pdf')
    assert text is not None
    assert len(text) > 0

def test_extract_docx():
    processor = DocumentProcessor()
    text = processor.extract_text('sample_docs/test.docx', 'docx')
    assert text is not None
    assert len(text) > 0
```

---

### 1.2 PDF Report Generation

**Priority**: HIGH  
**Effort**: 12 hours  
**Files to Create**:
- `nis2_agents/report_generator.py` (new)

**Implementation:**

```python
# nis2_agents/report_generator.py
"""
PDF Report Generation for NIS2 Compliance Audits
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import plotly.graph_objects as go
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NIS2ReportGenerator:
    """Generate professional PDF reports for compliance audits"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=12,
            spaceBefore=12
        ))
    
    def generate_report(self, audit, output_path: str) -> bool:
        """
        Generate complete NIS2 compliance report
        
        Args:
            audit: ComplianceAudit instance
            output_path: Path to save PDF
        
        Returns:
            True if successful, False otherwise
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            story = []
            
            # Cover Page
            story.extend(self._create_cover_page(audit))
            story.append(PageBreak())
            
            # Executive Summary
            story.extend(self._create_executive_summary(audit))
            story.append(PageBreak())
            
            # Compliance Score Overview
            story.extend(self._create_compliance_overview(audit))
            story.append(PageBreak())
            
            # Gap Analysis Details
            story.extend(self._create_gap_analysis(audit))
            story.append(PageBreak())
            
            # Recommendations
            story.extend(self._create_recommendations(audit))
            story.append(PageBreak())
            
            # Implementation Roadmap
            story.extend(self._create_implementation_roadmap(audit))
            
            # Build PDF
            doc.build(story)
            
            logger.info(f"Report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return False
    
    def _create_cover_page(self, audit):
        """Create report cover page"""
        elements = []
        
        # Title
        title = Paragraph(
            "NIS2 Compliance Audit Report",
            self.styles['CustomTitle']
        )
        elements.append(title)
        elements.append(Spacer(1, 2*cm))
        
        # Client Info
        client_info = f"""
        <b>Client:</b> {audit.client.company_name}<br/>
        <b>KVK Number:</b> {audit.client.kvk_number}<br/>
        <b>Sector:</b> {audit.client.get_sector_display()}<br/>
        <b>Company Size:</b> {audit.client.get_company_size_display()}<br/>
        <br/>
        <b>Audit Date:</b> {audit.created_at.strftime('%d %B %Y')}<br/>
        <b>Report Generated:</b> {datetime.now().strftime('%d %B %Y')}<br/>
        <b>Tier:</b> {audit.get_tier_display()}
        """
        
        elements.append(Paragraph(client_info, self.styles['Normal']))
        elements.append(Spacer(1, 3*cm))
        
        # Compliance Score (Large)
        score_text = f"""
        <para align="center">
            <font size="48" color="#2c5aa0"><b>{audit.compliance_score}%</b></font><br/>
            <font size="16">Overall Compliance Score</font>
        </para>
        """
        elements.append(Paragraph(score_text, self.styles['Normal']))
        
        return elements
    
    def _create_executive_summary(self, audit):
        """Create executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Get gaps by severity
        critical_gaps = audit.gaps.filter(severity='CRITICAL').count()
        high_gaps = audit.gaps.filter(severity='HIGH').count()
        medium_gaps = audit.gaps.filter(severity='MEDIUM').count()
        low_gaps = audit.gaps.filter(severity='LOW').count()
        
        summary_text = f"""
        This report presents the findings of a comprehensive NIS2 Directive compliance 
        assessment for {audit.client.company_name}. The audit was conducted on 
        {audit.created_at.strftime('%d %B %Y')} and evaluated the organization's 
        current security posture against the requirements of the NIS2 Directive.
        <br/><br/>
        <b>Key Findings:</b><br/>
        • Overall Compliance Score: <b>{audit.compliance_score}%</b><br/>
        • Total Gaps Identified: <b>{audit.gaps_identified}</b><br/>
        • Critical Issues: <b>{critical_gaps}</b><br/>
        • High Priority Issues: <b>{high_gaps}</b><br/>
        • Medium Priority Issues: <b>{medium_gaps}</b><br/>
        • Low Priority Issues: <b>{low_gaps}</b><br/>
        <br/>
        The following sections provide detailed analysis of each compliance gap, 
        along with specific recommendations for remediation.
        """
        
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        
        return elements
    
    def _create_compliance_overview(self, audit):
        """Create compliance score overview with charts"""
        elements = []
        
        elements.append(Paragraph("Compliance Overview", self.styles['SectionHeader']))
        
        # Category breakdown table
        categories = {}
        for gap in audit.gaps.all():
            if gap.category not in categories:
                categories[gap.category] = {'count': 0, 'avg_risk': 0}
            categories[gap.category]['count'] += 1
            categories[gap.category]['avg_risk'] += gap.risk_score
        
        # Calculate averages
        for cat in categories:
            categories[cat]['avg_risk'] /= categories[cat]['count']
        
        # Create table
        table_data = [['Category', 'Gaps Found', 'Avg Risk Score']]
        for cat, data in sorted(categories.items(), key=lambda x: x[1]['count'], reverse=True):
            table_data.append([
                cat.replace('_', ' ').title(),
                str(data['count']),
                f"{data['avg_risk']:.1f}/10"
            ])
        
        table = Table(table_data, colWidths=[8*cm, 3*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_gap_analysis(self, audit):
        """Create detailed gap analysis section"""
        elements = []
        
        elements.append(Paragraph("Detailed Gap Analysis", self.styles['SectionHeader']))
        
        # Group gaps by severity
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            gaps = audit.gaps.filter(severity=severity).order_by('-risk_score')
            
            if gaps.exists():
                severity_header = Paragraph(
                    f"{severity} Priority Gaps ({gaps.count()})",
                    self.styles['Heading3']
                )
                elements.append(severity_header)
                elements.append(Spacer(1, 0.5*cm))
                
                for gap in gaps:
                    gap_text = f"""
                    <b>{gap.title}</b><br/>
                    <i>NIS2 Reference: {gap.nis2_article}</i><br/>
                    <br/>
                    <b>Current State:</b> {gap.current_state}<br/>
                    <b>Required State:</b> {gap.required_state}<br/>
                    <br/>
                    <b>Recommendation:</b> {gap.recommendation}<br/>
                    <br/>
                    <b>Estimated Effort:</b> {gap.estimated_effort_hours} hours<br/>
                    <b>Risk Score:</b> {gap.risk_score}/10<br/>
                    """
                    
                    elements.append(Paragraph(gap_text, self.styles['Normal']))
                    elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_recommendations(self, audit):
        """Create recommendations section"""
        elements = []
        
        elements.append(Paragraph("Priority Recommendations", self.styles['SectionHeader']))
        
        # Get top 5 critical gaps
        critical_gaps = audit.gaps.filter(severity='CRITICAL').order_by('-risk_score')[:5]
        
        if critical_gaps.exists():
            rec_text = """
            Based on the compliance assessment, we recommend addressing the following 
            critical issues immediately:<br/><br/>
            """
            
            for i, gap in enumerate(critical_gaps, 1):
                rec_text += f"""
                <b>{i}. {gap.title}</b><br/>
                {gap.recommendation}<br/>
                <i>Estimated effort: {gap.estimated_effort_hours} hours</i><br/><br/>
                """
            
            elements.append(Paragraph(rec_text, self.styles['Normal']))
        
        return elements
    
    def _create_implementation_roadmap(self, audit):
        """Create implementation roadmap"""
        elements = []
        
        elements.append(Paragraph("Implementation Roadmap", self.styles['SectionHeader']))
        
        roadmap_text = """
        We recommend implementing the identified improvements in the following phases:<br/><br/>
        
        <b>Phase 1 (Weeks 1-4): Critical Issues</b><br/>
        Address all CRITICAL severity gaps to mitigate immediate risks.<br/><br/>
        
        <b>Phase 2 (Weeks 5-12): High Priority</b><br/>
        Implement HIGH severity recommendations to achieve baseline compliance.<br/><br/>
        
        <b>Phase 3 (Weeks 13-24): Medium Priority</b><br/>
        Address MEDIUM severity gaps to strengthen security posture.<br/><br/>
        
        <b>Phase 4 (Ongoing): Continuous Improvement</b><br/>
        Implement LOW severity recommendations and maintain compliance.<br/><br/>
        
        <b>Total Estimated Effort:</b> {total_hours} hours<br/>
        <b>Recommended Timeline:</b> 6 months
        """.format(
            total_hours=sum(gap.estimated_effort_hours for gap in audit.gaps.all())
        )
        
        elements.append(Paragraph(roadmap_text, self.styles['Normal']))
        
        return elements
```

**Integration with Orchestrator:**

```python
# In nis2_agents/orchestrator.py
from .report_generator import NIS2ReportGenerator

class NIS2Orchestrator:
    def __init__(self):
        self.qdrant = NIS2QdrantClient()
        self.auditor = NIS2Auditor()
        self.doc_processor = DocumentProcessor()
        self.report_gen = NIS2ReportGenerator()  # Add this
    
    def process_audit(self, audit_id: str) -> dict:
        # ... existing processing logic ...
        
        # Step 6: Generate PDF report
        if audit.tier in ['T1', 'T2', 'T3']:
            report_filename = f"NIS2_Report_{audit.client.company_name}_{audit.id}.pdf"
            report_path = settings.REPORT_OUTPUT_DIR / report_filename
            
            if self.report_gen.generate_report(audit, str(report_path)):
                audit.report_file = f"reports/{report_filename}"
                audit.report_generated = True
                audit.report_generated_at = timezone.now()
                audit.save()
```

---

### 1.3 Security Gatekeeper Agent

**Priority**: HIGH  
**Effort**: 10 hours  
**Files to Create**:
- `nis2_agents/security_gatekeeper.py` (new)

**Implementation:**

```python
# nis2_agents/security_gatekeeper.py
"""
Security Gatekeeper Agent
Validates documents for viruses and PII before processing
"""
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import Dict, List
import logging
import hashlib

logger = logging.getLogger(__name__)


class SecurityGatekeeper:
    """
    Security validation for uploaded documents
    - PII detection and anonymization
    - File validation
    - Security scanning
    """
    
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
    
    def scan_document(self, document) -> Dict:
        """
        Perform security scan on uploaded document
        
        Args:
            document: ClientDocument instance
        
        Returns:
            dict with scan results
        """
        results = {
            'safe': True,
            'virus_found': False,
            'pii_detected': False,
            'pii_types': [],
            'file_valid': True,
            'errors': []
        }
        
        try:
            # 1. File validation
            if not self._validate_file_type(document.original_filename):
                results['safe'] = False
                results['file_valid'] = False
                results['errors'].append('Invalid file type')
                return results
            
            # 2. File size check
            if document.file_size_bytes > 50 * 1024 * 1024:  # 50MB
                results['safe'] = False
                results['errors'].append('File too large')
                return results
            
            # 3. PII detection (if text extracted)
            if hasattr(document, 'extracted_text') and document.extracted_text:
                pii_results = self.detect_pii(document.extracted_text)
                if pii_results['found']:
                    results['pii_detected'] = True
                    results['pii_types'] = pii_results['types']
                    document.pii_detected = True
            
            # 4. Virus scan (placeholder - would integrate ClamAV)
            # results['virus_found'] = self._scan_virus(document.file.path)
            document.virus_scanned = True
            
            document.save()
            
        except Exception as e:
            logger.error(f"Error scanning document: {e}")
            results['safe'] = False
            results['errors'].append(str(e))
        
        return results
    
    def detect_pii(self, text: str) -> Dict:
        """
        Detect PII in text using Presidio
        
        Args:
            text: Text to analyze
        
        Returns:
            dict with PII detection results
        """
        try:
            # Analyze text for PII
            results = self.analyzer.analyze(
                text=text,
                language='en',
                entities=[
                    'PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER',
                    'IBAN_CODE', 'CREDIT_CARD', 'IP_ADDRESS',
                    'NL_BSN'  # Dutch social security number
                ]
            )
            
            pii_types = list(set([result.entity_type for result in results]))
            
            return {
                'found': len(results) > 0,
                'types': pii_types,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error detecting PII: {e}")
            return {'found': False, 'types': [], 'count': 0}
    
    def anonymize_pii(self, text: str) -> str:
        """
        Anonymize PII in text
        
        Args:
            text: Text containing PII
        
        Returns:
            Anonymized text
        """
        try:
            # Analyze
            analyzer_results = self.analyzer.analyze(
                text=text,
                language='en',
                entities=['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER']
            )
            
            # Anonymize
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results
            )
            
            return anonymized_result.text
            
        except Exception as e:
            logger.error(f"Error anonymizing PII: {e}")
            return text
    
    def _validate_file_type(self, filename: str) -> bool:
        """Validate file extension"""
        allowed_extensions = ['.pdf', '.docx', '.txt', '.doc']
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
```

---

## Phase 2: Testing & Quality (Week 3)

### 2.1 Comprehensive Test Suite

**Create test structure:**

```bash
tests/
├── __init__.py
├── test_models.py
├── test_api.py
├── test_auditor.py
├── test_orchestrator.py
├── test_rag_engine.py
├── test_document_processor.py
├── test_security_gatekeeper.py
└── test_report_generator.py
```

**Example: Model Tests**

```python
# tests/test_models.py
import pytest
from django.test import TestCase
from compliance_engine.models import Client, ComplianceAudit, ComplianceGap
from django.contrib.auth.models import User


class ClientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client = Client.objects.create(
            company_name="Test MSP BV",
            kvk_number="12345678",
            sector="MSP",
            company_size="MEDIUM",
            contact_person="John Doe",
            email="john@testmsp.nl",
            address="Test Street 1",
            city="Amsterdam",
            postal_code="1000AA",
            account_manager=self.user
        )
    
    def test_client_creation(self):
        self.assertEqual(self.client.company_name, "Test MSP BV")
        self.assertEqual(self.client.kvk_number, "12345678")
    
    def test_client_str(self):
        expected = "Test MSP BV (12345678)"
        self.assertEqual(str(self.client), expected)
    
    def test_uuid_primary_key(self):
        self.assertIsNotNone(self.client.id)
        self.assertEqual(len(str(self.client.id)), 36)  # UUID format


class ComplianceAuditModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client = Client.objects.create(
            company_name="Test Company",
            kvk_number="87654321",
            sector="HOSTING",
            company_size="SMALL",
            contact_person="Jane Doe",
            email="jane@test.nl",
            address="Test 2",
            city="Rotterdam",
            postal_code="2000BB",
            account_manager=self.user
        )
        self.audit = ComplianceAudit.objects.create(
            client=self.client,
            tier="T1",
            quoted_price=950.00
        )
    
    def test_audit_creation(self):
        self.assertEqual(self.audit.status, 'INTAKE')
        self.assertEqual(self.audit.tier, 'T1')
        self.assertEqual(float(self.audit.quoted_price), 950.00)
    
    def test_audit_relationships(self):
        self.assertEqual(self.audit.client, self.client)
        self.assertIn(self.audit, self.client.audits.all())
```

**Example: API Tests**

```python
# tests/test_api.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from compliance_engine.models import Client, ComplianceAudit


class ClientAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.force_authenticate(user=self.user)
    
    def test_create_client(self):
        data = {
            'company_name': 'New MSP',
            'kvk_number': '99999999',
            'sector': 'MSP',
            'company_size': 'MEDIUM',
            'contact_person': 'Test Person',
            'email': 'test@newmsp.nl',
            'address': 'Street 1',
            'city': 'Amsterdam',
            'postal_code': '1000AA'
        }
        
        response = self.client.post('/api/clients/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Client.objects.count(), 1)
        self.assertEqual(Client.objects.get().company_name, 'New MSP')
    
    def test_list_clients(self):
        Client.objects.create(
            company_name="Test Client",
            kvk_number="11111111",
            sector="CLOUD",
            company_size="LARGE",
            contact_person="Person",
            email="person@test.nl",
            address="Addr",
            city="City",
            postal_code="1234AB",
            account_manager=self.user
        )
        
        response = self.client.get('/api/clients/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
```

---

## Phase 3: Performance Optimization (Week 4)

### 3.1 Async Task Processing with Celery

**Install Celery:**
```bash
pip install celery redis
```

**Configuration:**

```python
# nis2_analyzer/celery.py
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nis2_analyzer.settings')

app = Celery('nis2_analyzer')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

```python
# nis2_analyzer/settings.py
# Celery Configuration
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Amsterdam'
```

**Create Async Tasks:**

```python
# nis2_agents/tasks.py
from celery import shared_task
from .orchestrator import NIS2Orchestrator
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_audit_async(self, audit_id: str):
    """
    Process audit asynchronously
    
    Args:
        audit_id: UUID of the audit to process
    
    Returns:
        dict with processing results
    """
    try:
        orchestrator = NIS2Orchestrator()
        result = orchestrator.process_audit(audit_id)
        return result
    
    except Exception as e:
        logger.error(f"Error processing audit {audit_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def generate_report_async(audit_id: str):
    """Generate PDF report asynchronously"""
    from compliance_engine.models import ComplianceAudit
    from .report_generator import NIS2ReportGenerator
    from django.conf import settings
    
    audit = ComplianceAudit.objects.get(id=audit_id)
    report_gen = NIS2ReportGenerator()
    
    report_filename = f"NIS2_Report_{audit.client.company_name}_{audit.id}.pdf"
    report_path = settings.REPORT_OUTPUT_DIR / report_filename
    
    if report_gen.generate_report(audit, str(report_path)):
        audit.report_file = f"reports/{report_filename}"
        audit.report_generated = True
        audit.save()
        return {'status': 'success', 'file': report_filename}
    
    return {'status': 'error'}
```

**Update API to use Celery:**

```python
# compliance_engine/views.py
from nis2_agents.tasks import process_audit_async

class ComplianceAuditViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        audit = self.get_object()
        
        if audit.status != 'INTAKE':
            return Response(
                {'error': 'Audit must be in INTAKE status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start async task
        task = process_audit_async.delay(str(audit.id))
        
        return Response({
            'message': 'Processing started',
            'audit_id': str(audit.id),
            'task_id': task.id,
            'status': 'QUEUED'
        }, status=status.HTTP_202_ACCEPTED)
    
    @action(detail=True, methods=['get'])
    def task_status(self, request, pk=None):
        """Check status of async task"""
        from celery.result import AsyncResult
        
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({'error': 'task_id required'}, status=400)
        
        task = AsyncResult(task_id)
        
        return Response({
            'task_id': task_id,
            'status': task.state,
            'result': task.result if task.ready() else None
        })
```

---

### 3.2 Redis Caching Layer

```python
# nis2_analyzer/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'nis2',
        'TIMEOUT': 3600,  # 1 hour default
    }
}

# Session storage in Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

**Cache expensive queries:**

```python
# dashboard/views.py
from django.views.decorators.cache import cache_page
from django.core.cache import cache


@cache_page(60 * 15)  # Cache for 15 minutes
def dashboard_stats(request):
    """Dashboard statistics with caching"""
    stats = {
        'total_audits': ComplianceAudit.objects.count(),
        'audits_this_month': ComplianceAudit.objects.filter(
            created_at__month=timezone.now().month
        ).count(),
        'avg_compliance_score': ComplianceAudit.objects.aggregate(
            avg=Avg('compliance_score')
        )['avg'],
        'revenue_this_month': ComplianceAudit.objects.filter(
            created_at__month=timezone.now().month
        ).aggregate(total=Sum('actual_price'))['total']
    }
    
    return JsonResponse(stats)


# Cache RAG results
def search_nis2_cached(query: str, top_k: int = 20):
    """Search with caching"""
    cache_key = f"rag:{hashlib.md5(query.encode()).hexdigest()}"
    
    cached_results = cache.get(cache_key)
    if cached_results:
        return cached_results
    
    # Perform search
    qdrant = NIS2QdrantClient()
    results = qdrant.search(query, top_k=top_k)
    
    # Cache for 1 hour
    cache.set(cache_key, results, timeout=3600)
    
    return results
```

---

## Phase 4: Advanced Features (Week 5-6)

### 4.1 Database Optimization

**Add indexes:**

```python
# compliance_engine/models.py
class ComplianceGap(models.Model):
    # ... existing fields ...
    
    class Meta:
        ordering = ['-severity', '-risk_score', 'category']
        indexes = [
            models.Index(fields=['audit', 'severity']),
            models.Index(fields=['category', '-risk_score']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['addressed', 'severity']),
        ]


class ComplianceAudit(models.Model):
    # ... existing fields ...
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-compliance_score']),
        ]
```

**Optimize queries:**

```python
# compliance_engine/views.py
class ComplianceAuditViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        """Optimized queryset with select_related"""
        return ComplianceAudit.objects.select_related('client').prefetch_related('gaps')


class ComplianceGapViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        """Optimized queryset"""
        queryset = ComplianceGap.objects.select_related('audit', 'audit__client')
        
        audit_id = self.request.query_params.get('audit_id')
        if audit_id:
            queryset = queryset.filter(audit_id=audit_id)
        
        return queryset
```

---

## Summary: Implementation Checklist

### Week 1-2: Core Features
- [ ] Document text extraction (PDF, DOCX, TXT)
- [ ] PDF report generation with ReportLab
- [ ] Security Gatekeeper (PII detection, file validation)
- [ ] Update orchestrator to use all components

### Week 3: Testing
- [ ] Unit tests for models (80% coverage target)
- [ ] API integration tests
- [ ] Agent tests with mocked LLMs
- [ ] Document processor tests
- [ ] Report generator tests

### Week 4: Performance
- [ ] Celery async task processing
- [ ] Redis caching layer
- [ ] Database query optimization
- [ ] Add database indexes

### Week 5-6: Polish
- [ ] Error handling improvements
- [ ] Logging and monitoring
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Admin interface customization
- [ ] Performance benchmarking

---

**Next Steps:**
1. Start with document extraction (highest priority)
2. Add PDF report generation
3. Implement comprehensive tests
4. Add async processing with Celery
5. Optimize with caching and indexes

**Estimated Total Effort**: 4-6 weeks (full-time)

---

**Last Updated**: March 2026  
**Status**: Implementation Guide for Production Readiness
