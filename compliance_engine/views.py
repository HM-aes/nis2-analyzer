"""
NIS2 Compliance Engine REST API Views
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from .models import Client, ComplianceAudit, ComplianceGap, ClientDocument
from .serializers import (
    ClientSerializer, ComplianceAuditSerializer, 
    ComplianceGapSerializer, ClientDocumentSerializer
)


class ClientViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing clients
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter clients by account manager if not superuser"""
        if self.request.user.is_superuser:
            return Client.objects.all()
        return Client.objects.filter(account_manager=self.request.user)


class ComplianceAuditViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing compliance audits
    """
    queryset = ComplianceAudit.objects.all()
    serializer_class = ComplianceAuditSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        """
        Trigger AI processing for an audit
        """
        audit = self.get_object()
        
        if audit.status != 'INTAKE':
            return Response(
                {'error': _('Audit must be in INTAKE status')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Import here to avoid circular imports
        from nis2_agents.orchestrator import NIS2Orchestrator
        
        # Start async processing
        orchestrator = NIS2Orchestrator()
        result = orchestrator.process_audit(audit.id)
        
        return Response({
            'message': _('Processing started'),
            'audit_id': str(audit.id),
            'status': result.get('status')
        })
    
    @action(detail=True, methods=['get'])
    def download_report(self, request, pk=None):
        """
        Download the generated PDF report
        """
        audit = self.get_object()
        
        if not audit.report_generated or not audit.report_file:
            return Response(
                {'error': _('Report not yet generated')},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return file download response
        from django.http import FileResponse
        return FileResponse(audit.report_file.open('rb'), 
                          as_attachment=True,
                          filename=f"NIS2_Report_{audit.client.company_name}.pdf")


class ComplianceGapViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing compliance gaps
    """
    queryset = ComplianceGap.objects.all()
    serializer_class = ComplianceGapSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter gaps by audit_id if provided"""
        queryset = ComplianceGap.objects.all()
        audit_id = self.request.query_params.get('audit_id')
        if audit_id:
            queryset = queryset.filter(audit_id=audit_id)
        return queryset


class ClientDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for uploading and managing client documents
    """
    queryset = ClientDocument.objects.all()
    serializer_class = ClientDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        """Save document with uploader info"""
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """
        Trigger processing for a specific document
        """
        document = self.get_object()
        
        # Import agents
        from nis2_agents.security_gatekeeper import SecurityGatekeeper
        
        # Process document
        gatekeeper = SecurityGatekeeper()
        result = gatekeeper.scan_document(document)
        
        return Response({
            'message': _('Document processed'),
            'document_id': str(document.id),
            'virus_found': result.get('virus_found', False),
            'pii_detected': result.get('pii_detected', False)
        })
