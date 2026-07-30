from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import render
from django.views import View

from .models import AssessmentLead


class LeadCaptureView(View):
    def post(self, request):
        email = request.POST.get("email", "").strip()
        try:
            validate_email(email)
        except ValidationError:
            return render(request, "marketing/_lead_form.html", {"error": "Enter a valid email address."})

        AssessmentLead.objects.get_or_create(email=email)
        return render(request, "marketing/_lead_confirmation.html", {"email": email})
