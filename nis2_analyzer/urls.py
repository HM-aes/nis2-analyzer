"""
NIS2 Analyzer URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard.views import DashboardLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("compliance_engine.urls")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    path("reports/", include("report_generator.urls", namespace="report_generator")),
    path("", DashboardLoginView.as_view(), name="home"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
