"""
Django Admin Configuration for NIS2 Compliance Engine
"""

from django.contrib import admin
from .models import Client, ComplianceAudit, ComplianceGap, ClientDocument, KnowledgeDocument


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'kvk_number', 'sector', 'company_size', 'contact_person']
    list_filter = ['sector', 'company_size']
    search_fields = ['company_name', 'kvk_number', 'contact_person']


@admin.register(ComplianceAudit)
class ComplianceAuditAdmin(admin.ModelAdmin):
    list_display = ['client', 'tier', 'status', 'compliance_score', 'created_at']
    list_filter = ['tier', 'status', 'report_generated']
    search_fields = ['client__company_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ComplianceGap)
class ComplianceGapAdmin(admin.ModelAdmin):
    list_display = ['title', 'audit', 'severity', 'category', 'risk_score', 'addressed']
    list_filter = ['severity', 'category', 'addressed']
    search_fields = ['title', 'description']


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'audit', 'document_type', 'processed', 'uploaded_at']
    list_filter = ['document_type', 'processed', 'virus_scanned']
    readonly_fields = ['uploaded_at', 'processed_at']


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'source', 'language', 'ingested', 'chunks_created']
    list_filter = ['source', 'language', 'ingested']
    search_fields = ['title']
