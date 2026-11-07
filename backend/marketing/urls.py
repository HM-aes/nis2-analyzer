from django.urls import path

from . import views

app_name = "marketing"

urlpatterns = [
    path("assessment/start/", views.LeadCaptureView.as_view(), name="lead_capture"),
]
