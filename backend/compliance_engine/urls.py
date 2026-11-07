"""
URL Configuration for Compliance Engine API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientViewSet, ComplianceAuditViewSet, 
    ComplianceGapViewSet, ClientDocumentViewSet
)

router = DefaultRouter()
router.register(r'clients', ClientViewSet)
router.register(r'audits', ComplianceAuditViewSet)
router.register(r'gaps', ComplianceGapViewSet)
router.register(r'documents', ClientDocumentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
