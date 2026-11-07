from django.contrib import admin

from .models import AssessmentLead


@admin.register(AssessmentLead)
class AssessmentLeadAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at")  # pyright: ignore[reportIncompatibleVariableOverride]
    search_fields = ("email",)
    ordering = ("-created_at",)
