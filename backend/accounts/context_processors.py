from django.conf import settings


def auth(request):
    return {
        "google_oauth_configured": bool(
            settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET
        ),
    }
