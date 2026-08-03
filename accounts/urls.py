from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("terms/", views.TermsView.as_view(), name="terms"),
    path("privacy/", views.PrivacyView.as_view(), name="privacy"),
    path(
        "password-reset/",
        views.PasswordResetPlaceholderView.as_view(),
        name="password_reset",
    ),
]
