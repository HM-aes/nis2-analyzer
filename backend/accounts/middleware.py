"""Site-wide login gate.

TEMPORARY: every page requires an authenticated user. The only things a
logged-out visitor can reach are the login page, the auth endpoints it needs
(allauth / Google OAuth), the Django admin login, and static/media assets.

To open a path back up to the public, add its prefix to ``PUBLIC_PREFIXES``.
Credentials (username + password) are managed separately for now via
``python backend/manage.py createsuperuser``.
"""

from django.contrib.auth.views import redirect_to_login


class LoginGateMiddleware:
    """Redirect every unauthenticated request to the login page."""

    # Path prefixes reachable without logging in.
    PUBLIC_PREFIXES = (
        "/login/",          # our login page
        "/accounts/",       # allauth: Google OAuth callbacks, etc.
        "/admin/login/",    # Django admin's own login form
        "/static/",
        "/media/",
        "/favicon.ico",     # redirects to the static SVG icon
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not self._is_public(request.path):
            return redirect_to_login(request.get_full_path())
        return self.get_response(request)

    def _is_public(self, path):
        return any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES)
