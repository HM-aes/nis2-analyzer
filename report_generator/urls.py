"""
Report Generator URL Configuration
"""

from django.urls import path
from . import views

app_name = 'report_generator'

urlpatterns = [
    # Public sector report (lead gen)
    path('sector/', views.SectorReportFormView.as_view(), name='sector_report'),
    # Authenticated: download gap analysis PDF
    path('audit/<uuid:pk>/download/', views.GapReportDownloadView.as_view(), name='gap_report_download'),
    # HTMX: status check / trigger
    path('audit/<uuid:pk>/generate/', views.GapReportGenerateView.as_view(), name='gap_report_generate'),
]
