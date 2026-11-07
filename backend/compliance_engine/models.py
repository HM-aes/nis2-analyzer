"""
NIS2 Compliance Engine Models
Database models for tracking clients, audits, gaps, and documents
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
import uuid


class Client(models.Model):
    """
    Dutch IT companies requiring NIS2 compliance
    """
    SECTOR_CHOICES = [
        ('MSP', _('Managed Service Provider')),
        ('HOSTING', _('Hosting Provider')),
        ('CLOUD', _('Cloud Service Provider')),
        ('TRANSPORT', _('Digital Transport')),
        ('ENERGY', _('Energy Sector')),
        ('HEALTHCARE', _('Healthcare IT')),
        ('FINANCE', _('Financial Services')),
        ('TELECOM', _('Telecommunications')),
        ('OTHER', _('Other Essential Service')),
    ]

    COMPANY_SIZE_CHOICES = [
        ('SMALL', _('10-49 employees')),
        ('MEDIUM', _('50-249 employees')),
        ('LARGE', _('250+ employees')),
    ]

    COUNTRY_CHOICES = [
        ('NL', _('Netherlands')),
        ('DE', _('Germany')),
        ('BE', _('Belgium')),
        ('FR', _('France')),
        ('ES', _('Spain')),
        ('IT', _('Italy')),
        ('PL', _('Poland')),
        ('SE', _('Sweden')),
        ('DK', _('Denmark')),
        ('FI', _('Finland')),
        ('AT', _('Austria')),
        ('IE', _('Ireland')),
        ('GB', _('United Kingdom')),
        ('OTHER', _('Other EU')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=200)
    kvk_number = models.CharField(max_length=8, unique=True, help_text="Dutch KVK number")
    sector = models.CharField(max_length=20, choices=SECTOR_CHOICES)
    company_size = models.CharField(max_length=10, choices=COMPANY_SIZE_CHOICES)
    country = models.CharField(max_length=10, choices=COUNTRY_CHOICES, default='NL')

    # Contact Information
    contact_person = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=10)
    
    # Relationship
    account_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_clients')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['company_name']
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
    
    def __str__(self):
        return f"{self.company_name} ({self.kvk_number})"


class ComplianceAudit(models.Model):
    """
    NIS2 compliance audit records
    Tracks the overall audit process and results
    """
    STATUS_CHOICES = [
        ('INTAKE', _('Document Intake')),
        ('PROCESSING', _('AI Processing')),
        ('ANALYSIS', _('Gap Analysis')),
        ('REVIEW', _('Human Review')),
        ('COMPLETE', _('Completed')),
        ('DELIVERED', _('Delivered to Client')),
    ]

    TIER_CHOICES = [
        ('T1', _('Tier 1 - Gap Analysis (€950)')),
        ('T2', _('Tier 2 - Implementation Docs (€2,500)')),
        ('T3', _('Tier 3 - Full Package (€5,000)')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='audits')
    tier = models.CharField(max_length=2, choices=TIER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INTAKE')
    
    # Uploaded Documents
    documents_uploaded = models.IntegerField(default=0)
    total_pages_processed = models.IntegerField(default=0)
    
    # AI Processing Results
    gaps_identified = models.IntegerField(default=0)
    compliance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                          help_text="0-100% compliance score")
    
    # Report Generation
    report_generated = models.BooleanField(default=False)
    report_file = models.FileField(upload_to='reports/%Y/%m/', null=True, blank=True,
                                   validators=[FileExtensionValidator(['pdf'])])
    report_generated_at = models.DateTimeField(null=True, blank=True)
    
    # Pricing
    quoted_price = models.DecimalField(max_digits=10, decimal_places=2)
    actual_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paid = models.BooleanField(default=False)
    
    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes
    internal_notes = models.TextField(blank=True, help_text="Internal consultant notes")
    client_feedback = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Compliance Audit')
        verbose_name_plural = _('Compliance Audits')
    
    def __str__(self):
        return f"{self.client.company_name} - {self.get_tier_display()} ({self.status})"
    
    @property
    def duration_days(self):
        """Calculate audit duration in days"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).days
        return None


class ComplianceGap(models.Model):
    """
    Individual NIS2 compliance gaps identified during audit
    """
    SEVERITY_CHOICES = [
        ('CRITICAL', _('Critical - Immediate Action Required')),
        ('HIGH', _('High - Must Address Before Certification')),
        ('MEDIUM', _('Medium - Should Address')),
        ('LOW', _('Low - Nice to Have')),
    ]

    CATEGORY_CHOICES = [
        ('TECHNICAL', _('Technical Controls')),
        ('ORGANIZATIONAL', _('Organizational Measures')),
        ('INCIDENT_RESPONSE', _('Incident Response')),
        ('SUPPLY_CHAIN', _('Supply Chain Security')),
        ('ENCRYPTION', _('Encryption & Cryptography')),
        ('ACCESS_CONTROL', _('Access Control')),
        ('LOGGING', _('Logging & Monitoring')),
        ('TRAINING', _('Security Awareness Training')),
        ('GOVERNANCE', _('Governance & Risk Management')),
        ('OTHER', _('Other')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(ComplianceAudit, on_delete=models.CASCADE, related_name='gaps')
    
    # Gap Details
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="What is missing or non-compliant")
    
    # NIS2 Reference
    nis2_article = models.CharField(max_length=50, help_text="e.g., Article 21.2")
    nis2_requirement = models.TextField(help_text="The actual NIS2 requirement text")
    
    # Current State vs Required State
    current_state = models.TextField(help_text="What the client currently has")
    required_state = models.TextField(help_text="What NIS2 requires")
    
    # Remediation
    recommendation = models.TextField(help_text="How to fix this gap")
    estimated_effort_hours = models.IntegerField(help_text="Estimated hours to implement")
    estimated_cost_euros = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Risk Assessment
    risk_score = models.IntegerField(help_text="1-10 risk score", default=5)
    business_impact = models.TextField(blank=True, help_text="Impact if not addressed")
    
    # Status Tracking
    addressed = models.BooleanField(default=False)
    addressed_date = models.DateField(null=True, blank=True)
    implementation_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-severity', '-risk_score', 'category']
        verbose_name = _('Compliance Gap')
        verbose_name_plural = _('Compliance Gaps')
    
    def __str__(self):
        return f"{self.get_severity_display()} - {self.title}"


class ClientDocument(models.Model):
    """
    Documents uploaded by clients for audit analysis
    """
    DOCUMENT_TYPE_CHOICES = [
        ('POLICY', _('Security Policy')),
        ('PROCEDURE', _('Security Procedure')),
        ('NETWORK_DIAGRAM', _('Network Diagram')),
        ('INCIDENT_PLAN', _('Incident Response Plan')),
        ('BCP', _('Business Continuity Plan')),
        ('RISK_ASSESSMENT', _('Risk Assessment')),
        ('AUDIT_REPORT', _('Previous Audit Report')),
        ('CERTIFICATE', _('Security Certificate')),
        ('OTHER', _('Other Document')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audit = models.ForeignKey(ComplianceAudit, on_delete=models.CASCADE, related_name='documents')
    
    # File Information
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(upload_to='client_documents/%Y/%m/',
                           validators=[FileExtensionValidator(['pdf', 'docx', 'txt'])])
    original_filename = models.CharField(max_length=255)
    file_size_bytes = models.BigIntegerField()
    
    # Processing Status
    processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True)
    pages_count = models.IntegerField(null=True, blank=True)
    text_extracted = models.BooleanField(default=False)
    
    # Security Scan Results
    virus_scanned = models.BooleanField(default=False)
    virus_found = models.BooleanField(default=False)
    pii_detected = models.BooleanField(default=False)
    pii_anonymized = models.BooleanField(default=False)
    
    # Content Analysis
    language_detected = models.CharField(max_length=10, blank=True)
    key_topics = models.JSONField(default=list, blank=True, help_text="AI-detected topics")
    relevance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                         help_text="0-100 relevance to NIS2")
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = _('Client Document')
        verbose_name_plural = _('Client Documents')
    
    def __str__(self):
        return f"{self.original_filename} ({self.get_document_type_display()})"


class KnowledgeDocument(models.Model):
    """
    NIS2 knowledge base documents stored in Qdrant
    Tracks which documents have been ingested into the RAG system
    """
    SOURCE_CHOICES = [
        ('NIS2_DIRECTIVE', _('NIS2 Directive (Official)')),
        ('CYBERBEVEILIGINGSWET', _('Dutch Cyberbeveiligingswet')),
        ('NCSC_FACTSHEET', _('NCSC-NL Factsheet')),
        ('ISO_27001', _('ISO 27001 Mapping')),
        ('ENISA_GUIDELINE', _('ENISA Guideline')),
        ('INTERNAL', _('Internal Knowledge')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Document Information
    title = models.CharField(max_length=300)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    language = models.CharField(max_length=2, choices=[('en', _('English')), ('nl', _('Dutch'))])
    url = models.URLField(blank=True, help_text="Source URL if available")
    file = models.FileField(upload_to='knowledge_base/', null=True, blank=True)
    
    # Processing Status
    ingested = models.BooleanField(default=False)
    ingested_at = models.DateTimeField(null=True, blank=True)
    chunks_created = models.IntegerField(default=0)
    qdrant_collection = models.CharField(max_length=100, default='nis2_knowledge_base')
    
    # Content Metadata
    total_pages = models.IntegerField(null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    version = models.CharField(max_length=50, blank=True)
    authority_level = models.IntegerField(default=5, help_text="1-10, higher = more authoritative")
    
    # Usage Statistics
    times_retrieved = models.IntegerField(default=0)
    last_retrieved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-authority_level', 'source', 'title']
        verbose_name = _('Knowledge Document')
        verbose_name_plural = _('Knowledge Documents')
    
    def __str__(self):
        return f"{self.title} ({self.get_source_display()})"
