from django.conf import settings


def _social_avatar_url(user):
    if not user.is_authenticated:
        return None
    account = user.socialaccount_set.filter(provider="google").first()
    return account.get_avatar_url() if account else None


def auth(request):
    return {
        "google_oauth_configured": bool(
            settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET
        ),
        "user_avatar_url": _social_avatar_url(request.user),
    }
