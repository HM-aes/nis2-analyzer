from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from .forms import LoginForm, SignupForm

DASHBOARD_URL = "dashboard:home"


def _is_htmx(request):
    return getattr(request, "htmx", False) or (
        request.headers.get("HX-Request") == "true"
    )


def _authenticate_login(request, identifier, password):
    """Accept username or email (e.g. createsuperuser vs signup accounts)."""
    identifier = identifier.strip()
    user = authenticate(request, username=identifier, password=password)
    if user is not None:
        return user
    try:
        user_obj = User.objects.get(email__iexact=identifier)
    except User.DoesNotExist:
        return None
    return authenticate(request, username=user_obj.username, password=password)


@require_http_methods(["GET", "POST"])
def home_view(request):
    """Landing page — includes signup form for the modal."""
    return render(request, "marketing/landing.html", {"form": SignupForm()})


@require_http_methods(["GET", "POST"])
def signup(request):
    if request.user.is_authenticated:
        return redirect(DASHBOARD_URL)

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            target = reverse(DASHBOARD_URL)
            if _is_htmx(request):
                resp = HttpResponse(status=204)
                resp["HX-Redirect"] = target
                return resp
            return redirect(DASHBOARD_URL)
        return render(request, "auth/_signup_form.html", {"form": form})

    form = SignupForm()
    if _is_htmx(request):
        return render(request, "auth/_signup_panel.html", {"form": form})
    return render(request, "auth/signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect(DASHBOARD_URL)

    next_url = request.GET.get("next") or request.POST.get("next") or ""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = _authenticate_login(
                request,
                form.cleaned_data["email"],
                form.cleaned_data["password"],
            )
            if user is not None:
                auth_login(request, user)
                target = next_url or reverse(DASHBOARD_URL)
                if _is_htmx(request):
                    resp = HttpResponse(status=204)
                    resp["HX-Redirect"] = target
                    return resp
                return redirect(target)
            form.add_error(None, _("Email or password is incorrect."))
        return render(
            request, "auth/_login_form.html", {"form": form, "next": next_url}
        )

    form = LoginForm()
    return render(request, "auth/login.html", {"form": form, "next": next_url})


class LegalPageView(TemplateView):
    """Placeholder until dedicated legal pages exist."""

    template_name = "auth/legal.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = self.page_title
        return ctx


class TermsView(LegalPageView):
    page_title = _("Terms of Service")


class PrivacyView(LegalPageView):
    page_title = _("Privacy Policy")


class PasswordResetPlaceholderView(TemplateView):
    template_name = "auth/legal.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = _("Reset password")
        return ctx
