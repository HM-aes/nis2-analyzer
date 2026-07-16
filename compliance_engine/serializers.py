"""
REST Framework Serializers for NIS2 Compliance Engine
"""

from rest_framework import serializers
from .models import Client, ComplianceAudit, ComplianceGap, ClientDocument


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ComplianceAuditSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    
    class Meta:
        model = ComplianceAudit
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'report_generated_at']


class ComplianceGapSerializer(serializers.ModelSerializer):
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = ComplianceGap
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = ClientDocument
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_at', 'processed_at', 'uploaded_by']
