"""
NIS2 Dashboard URL Configuration
"""

from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
from . import views

app_name = "dashboard"

urlpatterns = [
    # Auth — legacy dashboard login URL redirects to the dedicated auth page
    path(
        "login/",
        RedirectView.as_view(url=reverse_lazy("login"), query_string=True),
        name="login",
    ),
    path("logout/", views.DashboardLogoutView.as_view(), name="logout"),
    # Main pages
    path("", views.DashboardHomeView.as_view(), name="home"),
    path("clients/", views.ClientsView.as_view(), name="clients"),
    path("clients/new/", views.NewClientView.as_view(), name="client_new"),
    path("clients/<uuid:pk>/", views.ClientDetailView.as_view(), name="client_detail"),
    path("clients/<uuid:pk>/edit/", views.ClientUpdateView.as_view(), name="client_update"),  # Task 3
    path("audits/", views.AuditsView.as_view(), name="audits"),
    path("audits/new/", views.NewAuditView.as_view(), name="audit_new"),  # Task 2
    path("audits/<uuid:pk>/", views.AuditDetailView.as_view(), name="audit_detail"),
    path("audits/<uuid:pk>/upload/", views.UploadDocumentView.as_view(), name="audit_upload"),
    path("audits/<uuid:pk>/run/", views.RunAuditView.as_view(), name="audit_run"),
    path("audits/<uuid:pk>/transition/", views.AuditTransitionView.as_view(), name="audit_transition"),  # Task 4
    path("gaps/", views.GapsView.as_view(), name="gaps"),
    path("gaps/<uuid:pk>/address/", views.GapAddressView.as_view(), name="gap_address"),  # Task 5
    path("documents/<uuid:pk>/delete/", views.DocumentDeleteView.as_view(), name="document_delete"),  # Task 6
    path("documents/<uuid:pk>/reprocess/", views.DocumentReprocessView.as_view(), name="document_reprocess"),  # Task 6
    # HTMX partials
    path(
        "htmx/audit-status/<uuid:pk>/",
        views.HtmxAuditStatus.as_view(),
        name="htmx_audit_status",
    ),
    path("htmx/gap-rows/", views.HtmxGapRows.as_view(), name="htmx_gap_rows"),
    path(
        "htmx/client-search/",
        views.HtmxClientSearch.as_view(),
        name="htmx_client_search",
    ),
    path("htmx/audit-rows/", views.HtmxAuditRows.as_view(), name="htmx_audit_rows"),
]
