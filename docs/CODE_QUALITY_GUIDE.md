# 💎 Code Quality & Best Practices Guide

## Overview

This document outlines the coding standards, design patterns, and best practices used in the NIS2 Compliance Analyzer project. These practices demonstrate production-ready, maintainable code suitable for enterprise environments.

---

## Table of Contents

1. [Python Code Standards](#python-code-standards)
2. [Django Best Practices](#django-best-practices)
3. [API Design Principles](#api-design-principles)
4. [Error Handling Patterns](#error-handling-patterns)
5. [Security Best Practices](#security-best-practices)
6. [Testing Strategies](#testing-strategies)
7. [Performance Optimization](#performance-optimization)
8. [Documentation Standards](#documentation-standards)

---

## Python Code Standards

### PEP 8 Compliance

**Always follow PEP 8** with these key points:

```python
# ✅ GOOD: Clear, descriptive names
class ComplianceAuditProcessor:
    def analyze_security_gaps(self, client_documents: List[str]) -> GapAnalysisOutput:
        """Analyze client documents for compliance gaps"""
        pass

# ❌ BAD: Unclear, abbreviated names
class CAP:
    def analyze(self, docs):
        pass
```

### Type Hints (Python 3.10+)

**Always use type hints** for function signatures:

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# ✅ GOOD: Full type annotations
def process_audit(
    audit_id: str,
    options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process compliance audit with type safety"""
    return {"status": "success", "audit_id": audit_id}

# ✅ GOOD: Pydantic models for complex types
class GapAnalysisOutput(BaseModel):
    gaps: List[ComplianceGapOutput]
    overall_compliance_score: float
    summary: str
    critical_priorities: List[str]

# ❌ BAD: No type hints
def process_audit(audit_id, options=None):
    return {"status": "success"}
```

### Docstrings (Google Style)

```python
def analyze_compliance(
    client_documents: str,
    nis2_requirements: List[str]
) -> GapAnalysisOutput:
    """
    Analyze client documents against NIS2 requirements.
    
    This function uses Claude AI via Pydantic AI to identify compliance
    gaps in a structured, type-safe manner.
    
    Args:
        client_documents: Extracted text from client's security documentation
        nis2_requirements: Retrieved NIS2 requirements from RAG (context)
    
    Returns:
        Structured gap analysis with identified issues
    
    Raises:
        AnthropicAPIError: If Claude API is unavailable
        ValidationError: If LLM output doesn't match schema
    
    Example:
        >>> auditor = NIS2Auditor()
        >>> result = auditor.analyze_compliance(
        ...     client_documents="Security policy text...",
        ...     nis2_requirements=["Article 21.2: ..."]
        ... )
        >>> print(result.overall_compliance_score)
        85.5
    """
    pass
```

### Error Handling

**Use specific exceptions** and proper logging:

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ✅ GOOD: Specific exceptions, proper logging
def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Extract text from PDF file"""
    try:
        with pdfplumber.open(file_path) as pdf:
            text_parts = [page.extract_text() for page in pdf.pages]
            return "\n\n".join(filter(None, text_parts))
    
    except FileNotFoundError:
        logger.error(f"PDF file not found: {file_path}")
        raise
    
    except pdfplumber.PDFSyntaxError as e:
        logger.error(f"Invalid PDF format: {file_path}, error: {e}")
        return None
    
    except Exception as e:
        logger.exception(f"Unexpected error extracting PDF: {file_path}")
        raise

# ❌ BAD: Bare except, no logging
def extract_text_from_pdf(file_path):
    try:
        # ... extraction logic
        pass
    except:
        return None
```

### Constants and Configuration

```python
# ✅ GOOD: Constants at module level, uppercase
MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
ALLOWED_FILE_EXTENSIONS = ['.pdf', '.docx', '.txt']
DEFAULT_COMPLIANCE_THRESHOLD = 85.0

# Configuration from environment
from django.conf import settings

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
QDRANT_HOST = settings.QDRANT_HOST

# ❌ BAD: Magic numbers in code
if file_size > 52428800:  # What is this number?
    raise ValueError("File too large")
```

---

## Django Best Practices

### Model Design

**Use UUIDs for primary keys** (security + distributed systems):

```python
import uuid
from django.db import models

class Client(models.Model):
    """
    ✅ GOOD: UUID primary key, clear field names, proper validation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=200)
    kvk_number = models.CharField(
        max_length=8, 
        unique=True, 
        help_text="Dutch KVK number"
    )
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['company_name']
        indexes = [
            models.Index(fields=['kvk_number']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.company_name} ({self.kvk_number})"
```

**Use model methods for business logic**:

```python
class ComplianceAudit(models.Model):
    # ... fields ...
    
    def mark_complete(self):
        """
        ✅ GOOD: Encapsulate business logic in model methods
        """
        if self.status != 'ANALYSIS':
            raise ValueError("Can only complete audits in ANALYSIS status")
        
        self.status = 'COMPLETE'
        self.completed_at = timezone.now()
        self.save()
        
        # Send notification
        self._send_completion_notification()
    
    def calculate_total_effort(self) -> int:
        """Calculate total implementation effort in hours"""
        return sum(gap.estimated_effort_hours for gap in self.gaps.all())
    
    @property
    def duration_days(self) -> Optional[int]:
        """Calculate audit duration"""
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).days
        return None
```

### QuerySet Optimization

**Avoid N+1 queries** with `select_related` and `prefetch_related`:

```python
# ❌ BAD: N+1 queries (1 + N database hits)
audits = ComplianceAudit.objects.all()
for audit in audits:
    print(audit.client.company_name)  # Database query for each audit!
    for gap in audit.gaps.all():      # Database query for each audit!
        print(gap.title)

# ✅ GOOD: Optimized with select_related and prefetch_related
audits = ComplianceAudit.objects.select_related('client').prefetch_related('gaps')
for audit in audits:
    print(audit.client.company_name)  # No extra query
    for gap in audit.gaps.all():      # No extra query
        print(gap.title)
```

**Use custom managers for common queries**:

```python
class ComplianceAuditQuerySet(models.QuerySet):
    """Custom queryset with business logic"""
    
    def in_progress(self):
        """Get audits currently being processed"""
        return self.filter(status__in=['PROCESSING', 'ANALYSIS'])
    
    def completed_this_month(self):
        """Get audits completed this month"""
        return self.filter(
            completed_at__month=timezone.now().month,
            status='COMPLETE'
        )
    
    def high_risk(self):
        """Get audits with compliance score < 70%"""
        return self.filter(compliance_score__lt=70)


class ComplianceAudit(models.Model):
    # ... fields ...
    
    objects = ComplianceAuditQuerySet.as_manager()


# Usage:
in_progress_audits = ComplianceAudit.objects.in_progress()
risky_audits = ComplianceAudit.objects.high_risk().select_related('client')
```

### Django REST Framework

**Use serializers properly**:

```python
from rest_framework import serializers

# ✅ GOOD: Explicit fields, validation, nested serializers
class ComplianceGapSerializer(serializers.ModelSerializer):
    """Serializer for compliance gaps"""
    
    severity_display = serializers.CharField(
        source='get_severity_display',
        read_only=True
    )
    category_display = serializers.CharField(
        source='get_category_display',
        read_only=True
    )
    
    class Meta:
        model = ComplianceGap
        fields = [
            'id', 'category', 'category_display', 'severity', 
            'severity_display', 'title', 'description', 'nis2_article',
            'current_state', 'required_state', 'recommendation',
            'estimated_effort_hours', 'risk_score', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_risk_score(self, value):
        """Validate risk score is between 1 and 10"""
        if not 1 <= value <= 10:
            raise serializers.ValidationError("Risk score must be between 1 and 10")
        return value


class ComplianceAuditSerializer(serializers.ModelSerializer):
    """Serializer for audits with nested gaps"""
    
    client_name = serializers.CharField(
        source='client.company_name',
        read_only=True
    )
    gaps = ComplianceGapSerializer(many=True, read_only=True)
    gap_count = serializers.IntegerField(
        source='gaps.count',
        read_only=True
    )
    
    class Meta:
        model = ComplianceAudit
        fields = '__all__'
```

**ViewSet best practices**:

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

class ComplianceAuditViewSet(viewsets.ModelViewSet):
    """
    ✅ GOOD: Proper permissions, optimized queryset, custom actions
    """
    queryset = ComplianceAudit.objects.select_related('client').prefetch_related('gaps')
    serializer_class = ComplianceAuditSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Non-superusers only see their own clients
        if not self.request.user.is_superuser:
            queryset = queryset.filter(client__account_manager=self.request.user)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        """Custom action to start audit processing"""
        audit = self.get_object()
        
        # Validation
        if audit.status != 'INTAKE':
            return Response(
                {'error': 'Audit must be in INTAKE status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Start async processing
        from nis2_agents.tasks import process_audit_async
        task = process_audit_async.delay(str(audit.id))
        
        return Response({
            'message': 'Processing started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
```

---

## API Design Principles

### RESTful Resource Naming

```
✅ GOOD:
GET    /api/clients/                    # List clients
POST   /api/clients/                    # Create client
GET    /api/clients/{id}/               # Get client
PUT    /api/clients/{id}/               # Update client
DELETE /api/clients/{id}/               # Delete client
POST   /api/audits/{id}/start_processing/  # Custom action

❌ BAD:
GET    /api/getClients
POST   /api/createClient
GET    /api/client?id=123
POST   /api/startAuditProcessing
```

### HTTP Status Codes

```python
# ✅ GOOD: Appropriate status codes
return Response(data, status=status.HTTP_200_OK)           # Success
return Response(data, status=status.HTTP_201_CREATED)      # Created
return Response(status=status.HTTP_204_NO_CONTENT)         # Deleted
return Response(data, status=status.HTTP_202_ACCEPTED)     # Async task queued
return Response(error, status=status.HTTP_400_BAD_REQUEST) # Validation error
return Response(error, status=status.HTTP_404_NOT_FOUND)   # Not found
return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # Server error
```

### Pagination

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Response format:
{
    "count": 100,
    "next": "http://api.example.com/clients/?page=2",
    "previous": null,
    "results": [...]
}
```

---

## Error Handling Patterns

### Layered Error Handling

```python
# Layer 1: Agent-level errors
class NIS2Auditor:
    async def analyze_compliance(self, client_documents: str, nis2_requirements: List[str]):
        try:
            result = await self.agent.run(context)
            return result.data
        
        except AnthropicAPIError as e:
            logger.error(f"Claude API error: {e}")
            raise  # Re-raise for orchestrator to handle
        
        except ValidationError as e:
            logger.error(f"Invalid LLM output: {e}")
            raise


# Layer 2: Orchestrator-level errors
class NIS2Orchestrator:
    def process_audit(self, audit_id: str) -> dict:
        try:
            # ... processing logic
            gap_analysis = self.auditor.analyze_compliance_sync(...)
            
        except AnthropicAPIError as e:
            audit.status = 'REVIEW'
            audit.processing_error = 'AI service temporarily unavailable'
            audit.save()
            
            # Alert ops team
            self._send_alert('Claude API failure', audit_id)
            
            return {
                'status': 'error',
                'message': 'AI analysis failed, marked for manual review'
            }
        
        except Exception as e:
            logger.exception(f"Unexpected error processing audit {audit_id}")
            audit.status = 'REVIEW'
            audit.save()
            return {'status': 'error', 'message': str(e)}


# Layer 3: API-level errors
class ComplianceAuditViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        try:
            audit = self.get_object()
            task = process_audit_async.delay(str(audit.id))
            return Response({'task_id': task.id}, status=202)
        
        except ComplianceAudit.DoesNotExist:
            return Response(
                {'error': 'Audit not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            logger.exception(f"Error starting audit processing")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

### Custom Exceptions

```python
# nis2_agents/exceptions.py
class NIS2Exception(Exception):
    """Base exception for NIS2 agents"""
    pass


class DocumentProcessingError(NIS2Exception):
    """Raised when document processing fails"""
    pass


class RAGRetrievalError(NIS2Exception):
    """Raised when RAG retrieval fails"""
    pass


class AIAnalysisError(NIS2Exception):
    """Raised when AI analysis fails"""
    pass


# Usage:
def extract_text(self, file_path: str) -> str:
    try:
        # ... extraction logic
        pass
    except Exception as e:
        raise DocumentProcessingError(f"Failed to extract text from {file_path}") from e
```

---

## Security Best Practices

### Input Validation

```python
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator

# ✅ GOOD: Validation at model level
class ClientDocument(models.Model):
    file = models.FileField(
        upload_to='client_documents/%Y/%m/',
        validators=[FileExtensionValidator(['pdf', 'docx', 'txt'])]
    )
    file_size_bytes = models.BigIntegerField(
        validators=[MaxValueValidator(50 * 1024 * 1024)]  # 50MB max
    )


class ComplianceGap(models.Model):
    risk_score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
```

### SQL Injection Prevention

```python
# ✅ GOOD: Use ORM (automatic parameterization)
clients = Client.objects.filter(kvk_number=user_input)

# ✅ GOOD: If raw SQL needed, use parameterization
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(
        "SELECT * FROM clients WHERE kvk_number = %s",
        [user_input]
    )

# ❌ BAD: String concatenation (SQL injection vulnerability!)
cursor.execute(f"SELECT * FROM clients WHERE kvk_number = '{user_input}'")
```

### XSS Prevention

```python
# ✅ GOOD: Django templates auto-escape by default
{{ client.company_name }}  # Automatically escaped

# ✅ GOOD: Explicit escaping in Python
from django.utils.html import escape
safe_text = escape(user_input)

# ❌ BAD: Marking unsafe content as safe
{{ user_input|safe }}  # Only if you're 100% sure it's safe!
```

### Secrets Management

```python
# ✅ GOOD: Environment variables
from decouple import config

ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY')
SECRET_KEY = config('SECRET_KEY')
DATABASE_URL = config('DATABASE_URL')

# ❌ BAD: Hardcoded secrets
ANTHROPIC_API_KEY = 'sk-ant-api03-...'  # NEVER DO THIS!
```

---

## Testing Strategies

### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from nis2_agents.auditor import NIS2Auditor, GapAnalysisOutput

class TestNIS2Auditor:
    """Unit tests for NIS2 Auditor agent"""
    
    @patch('nis2_agents.auditor.Agent')
    def test_analyze_compliance_returns_valid_output(self, mock_agent):
        """Test that auditor returns valid structured output"""
        # Arrange
        mock_result = Mock()
        mock_result.data = GapAnalysisOutput(
            gaps=[],
            overall_compliance_score=85.5,
            summary="Good compliance posture",
            critical_priorities=["Implement MFA", "Update firewall rules"]
        )
        mock_agent.return_value.run.return_value = mock_result
        
        auditor = NIS2Auditor()
        
        # Act
        result = auditor.analyze_compliance_sync(
            client_documents="Test security policy",
            nis2_requirements=["Article 21.2: Essential entities shall..."]
        )
        
        # Assert
        assert result.overall_compliance_score == 85.5
        assert len(result.critical_priorities) == 2
        assert "MFA" in result.critical_priorities[0]
    
    def test_analyze_compliance_validates_risk_scores(self):
        """Test that risk scores are validated (1-10)"""
        # This would test Pydantic validation
        with pytest.raises(ValidationError):
            ComplianceGapOutput(
                title="Test",
                category="TECHNICAL",
                severity="HIGH",
                nis2_article="21.2",
                current_state="None",
                required_state="MFA",
                recommendation="Implement MFA",
                risk_score=15,  # Invalid! Must be 1-10
                estimated_effort_hours=40
            )
```

### Integration Tests

```python
from django.test import TestCase
from rest_framework.test import APIClient
from compliance_engine.models import Client, ComplianceAudit

class AuditAPIIntegrationTest(TestCase):
    """Integration tests for audit API"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('test', 'test@example.com', 'password')
        self.client.force_authenticate(user=self.user)
        
        self.test_client = Client.objects.create(
            company_name="Test MSP",
            kvk_number="12345678",
            sector="MSP",
            company_size="MEDIUM",
            contact_person="John Doe",
            email="john@testmsp.nl",
            address="Test St 1",
            city="Amsterdam",
            postal_code="1000AA",
            account_manager=self.user
        )
    
    def test_create_audit_workflow(self):
        """Test complete audit creation workflow"""
        # Create audit
        response = self.client.post('/api/audits/', {
            'client': str(self.test_client.id),
            'tier': 'T1',
            'quoted_price': 950.00
        })
        
        self.assertEqual(response.status_code, 201)
        audit_id = response.data['id']
        
        # Verify audit created
        audit = ComplianceAudit.objects.get(id=audit_id)
        self.assertEqual(audit.status, 'INTAKE')
        self.assertEqual(audit.tier, 'T1')
        
        # Verify in database
        self.assertEqual(ComplianceAudit.objects.count(), 1)
```

### Test Coverage

```bash
# Run tests with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report

# Target: >80% coverage
```

---

## Performance Optimization

### Database Query Optimization

```python
# ✅ GOOD: Use select_related for ForeignKey
audits = ComplianceAudit.objects.select_related('client')

# ✅ GOOD: Use prefetch_related for reverse ForeignKey / ManyToMany
audits = ComplianceAudit.objects.prefetch_related('gaps')

# ✅ GOOD: Combine both
audits = ComplianceAudit.objects.select_related('client').prefetch_related('gaps')

# ✅ GOOD: Use only() to fetch specific fields
clients = Client.objects.only('company_name', 'kvk_number')

# ✅ GOOD: Use defer() to exclude large fields
documents = ClientDocument.objects.defer('file')
```

### Caching

```python
from django.core.cache import cache
from django.views.decorators.cache import cache_page
import hashlib

# ✅ GOOD: Cache expensive computations
def get_dashboard_stats():
    cache_key = 'dashboard_stats'
    stats = cache.get(cache_key)
    
    if stats is None:
        stats = {
            'total_audits': ComplianceAudit.objects.count(),
            'avg_score': ComplianceAudit.objects.aggregate(Avg('compliance_score'))
        }
        cache.set(cache_key, stats, timeout=900)  # 15 minutes
    
    return stats

# ✅ GOOD: Cache view
@cache_page(60 * 15)  # 15 minutes
def dashboard_view(request):
    return render(request, 'dashboard.html', get_dashboard_stats())

# ✅ GOOD: Cache RAG results
def search_nis2_requirements(query: str):
    cache_key = f"rag:{hashlib.md5(query.encode()).hexdigest()}"
    results = cache.get(cache_key)
    
    if results is None:
        results = qdrant.search(query, top_k=20)
        cache.set(cache_key, results, timeout=3600)  # 1 hour
    
    return results
```

### Async Processing

```python
from celery import shared_task

# ✅ GOOD: Long-running tasks in Celery
@shared_task(bind=True, max_retries=3)
def process_audit_async(self, audit_id: str):
    """Process audit asynchronously"""
    try:
        orchestrator = NIS2Orchestrator()
        result = orchestrator.process_audit(audit_id)
        return result
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

# API returns immediately
task = process_audit_async.delay(audit_id)
return Response({'task_id': task.id}, status=202)
```

---

## Documentation Standards

### Code Comments

```python
# ✅ GOOD: Explain WHY, not WHAT
# Use Pydantic AI instead of raw Claude API to ensure type-safe outputs
# This eliminates parsing errors in production
auditor = NIS2Auditor()

# Calculate compliance score as weighted average
# Critical gaps: 40%, High: 30%, Medium: 20%, Low: 10%
compliance_score = calculate_weighted_score(gaps)

# ❌ BAD: Obvious comments
# Create a client
client = Client.objects.create(...)

# Loop through gaps
for gap in gaps:
    pass
```

### API Documentation

```python
from rest_framework.decorators import api_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

@swagger_auto_schema(
    method='post',
    operation_description="Start processing a compliance audit",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'audit_id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid')
        }
    ),
    responses={
        202: openapi.Response('Processing started', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'task_id': openapi.Schema(type=openapi.TYPE_STRING),
                'status': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )),
        400: 'Bad request',
        404: 'Audit not found'
    }
)
@api_view(['POST'])
def start_audit_processing(request):
    """Start async processing for an audit"""
    pass
```

---

## Summary: Code Quality Checklist

### Before Committing Code

- [ ] **Type hints** on all function signatures
- [ ] **Docstrings** for all public functions/classes
- [ ] **Error handling** with specific exceptions
- [ ] **Logging** for important operations
- [ ] **Tests** for new functionality (unit + integration)
- [ ] **No hardcoded secrets** or magic numbers
- [ ] **PEP 8 compliant** (run `flake8` or `black`)
- [ ] **Optimized queries** (no N+1 queries)
- [ ] **Security validated** (input validation, SQL injection prevention)
- [ ] **Documentation updated** (README, API docs)

### Code Review Checklist

- [ ] Code is readable and maintainable
- [ ] Business logic is in the right layer (models, not views)
- [ ] Error handling is comprehensive
- [ ] Tests cover edge cases
- [ ] Performance is acceptable (no obvious bottlenecks)
- [ ] Security vulnerabilities addressed
- [ ] Documentation is clear and accurate

---

**Last Updated**: March 2026  
**Status**: Production-Ready Code Standards
