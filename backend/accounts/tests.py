from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser, User
from django.db import OperationalError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.views import signup


class AuthDatabaseErrorTests(TestCase):
    def test_login_shows_friendly_error_when_auth_table_missing(self):
        with patch(
            "accounts.views._authenticate_login",
            side_effect=OperationalError("no such table: auth_user"),
        ):
            response = self.client.post(
                reverse("login"),
                {"email": "admin", "password": "admin123"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "temporarily unavailable")
        self.assertContains(response, "role=\"alert\"")

    def test_wrong_password_still_shows_credentials_error(self):
        User.objects.create_user(
            username="admin", email="admin@nis2.local", password="admin123"
        )
        response = self.client.post(
            reverse("login"),
            {"email": "admin", "password": "nope"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "incorrect")

    def test_signup_shows_friendly_error_when_auth_table_missing(self):
        request = RequestFactory().post(
            reverse("signup"),
            {
                "email": "new@org.eu",
                "organisation": "Acme",
                "password1": "passphrase-long",
            },
        )
        request.user = AnonymousUser()
        request.htmx = False
        with patch(
            "accounts.forms.SignupForm.save",
            side_effect=OperationalError("no such table: auth_user"),
        ):
            response = signup(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "database is not ready")
