"""
Django settings for NIS2 Compliance Analyzer
"""

import os
from pathlib import Path
from typing import Any

import dj_database_url
from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent


def _parse_csv_hosts(value: str) -> list[str]:
    """Parse comma-separated hosts; tolerate Railway env var mistakes."""
    value = value.strip().strip('"').strip("'")
    if value.upper().startswith("ALLOWED_HOSTS="):
        value = value.split("=", 1)[1].strip()
    hosts = []
    for part in value.split(","):
        host = part.strip().strip('"').strip("'")
        if host:
            hosts.append(host)
    return hosts


def _parse_csv_origins(value: str) -> list[str]:
    return [s.strip() for s in value.split(",") if s.strip()]


# Security
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-CHANGE-THIS-IN-PRODUCTION",
)
DEBUG = config("DEBUG", default=True, cast=bool)

_database_url: str = str(config("DATABASE_URL", default=""))
ALLOWED_HOSTS: list[str] = _parse_csv_hosts(
    str(config("ALLOWED_HOSTS", default="localhost,127.0.0.1")),
)
# Railway — accept the service public domain and any *.up.railway.app host
_railway_domain: str = (
    os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
    or str(config("RAILWAY_PUBLIC_DOMAIN", default=""))
).strip().strip('"').strip("'")
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_railway_domain)
_on_railway = any(
    os.environ.get(key)
    for key in (
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_PUBLIC_DOMAIN",
        "RAILWAY_SERVICE_ID",
        "RAILWAY_PROJECT_ID",
    )
) or bool(_database_url)
if _on_railway and ".up.railway.app" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".up.railway.app")

# HTTPS / CSRF — required for Railway (TLS terminates at the edge proxy)
CSRF_TRUSTED_ORIGINS: list[str] = _parse_csv_origins(
    str(config("CSRF_TRUSTED_ORIGINS", default="")),
)
if _railway_domain:
    _railway_origin = f"https://{_railway_domain}"
    if _railway_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_railway_origin)
elif _on_railway and "https://*.up.railway.app" not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append("https://*.up.railway.app")

if _database_url:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    # Third party
    "rest_framework",
    "django_htmx",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # NIS2 Apps
    "compliance_engine",
    "nis2_agents",
    "rag_engine",
    "dashboard",
    "report_generator",
    "marketing",
    "accounts.apps.AccountsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nis2_analyzer.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.auth",
            ],
        },
    },
]

WSGI_APPLICATION = "nis2_analyzer.wsgi.application"

# Database — PostgreSQL on Railway (DATABASE_URL),
# SQLite locally
if _database_url:
    DATABASES = {
        "default": dj_database_url.parse(
            _database_url,
            conn_max_age=600,
        ),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

# Internationalization
LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
_railway_deploy = any(
    os.environ.get(key)
    for key in (
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_PUBLIC_DOMAIN",
        "RAILWAY_SERVICE_ID",
        "RAILWAY_PROJECT_ID",
    )
)
if DEBUG or not _railway_deploy:
    # Serve from static/ locally — no collectstatic after every asset edit
    STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    WHITENOISE_USE_FINDERS = True
    WHITENOISE_MAX_AGE = 0  # no 304/cache in dev — always serve fresh CSS/JS
    # Rescan static/ on every request so new/moved files (e.g. a freshly
    # added component folder) are picked up without restarting the server.
    # WhiteNoise otherwise indexes static/ once at startup and 404s anything
    # added afterwards — this matters here since DEBUG can be False locally.
    WHITENOISE_AUTOREFRESH = True
else:
    STATICFILES_STORAGE = (
        "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1

SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="")

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": GOOGLE_CLIENT_ID,
                "secret": GOOGLE_CLIENT_SECRET,
                "key": "",
            }
        ],
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
    }
}

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 20,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# ═══════════════════════════════════════════════════════════
# NIS2 SPECIFIC CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Qdrant Configuration
QDRANT_HOST = config("QDRANT_HOST", default="localhost")
QDRANT_PORT = config("QDRANT_PORT", default=6333, cast=int)
QDRANT_API_KEY = config("QDRANT_API_KEY", default="")
QDRANT_COLLECTION_NAME = "nis2_knowledge_base"
QDRANT_VECTOR_SIZE = 384  # sentence-transformers/all-MiniLM-L6-v2
# Local on-disk mode for dev; None in production
# (uses QDRANT_HOST/PORT instead)
QDRANT_LOCAL_PATH = None if _database_url else BASE_DIR / "qdrant_local"

# AI API Keys
GOOGLE_API_KEY = config("GOOGLE_API_KEY", default="")

# Embedding Model (fastembed — BAAI/bge-small-en-v1.5, 384-dim)
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Document Processing
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_DOCUMENT_TYPES = [".pdf", ".docx", ".txt", ".md"]

# NIS2 Report Configuration
REPORT_TEMPLATES_DIR = BASE_DIR / "templates" / "reports"
REPORT_OUTPUT_DIR = MEDIA_ROOT / "reports"
REPORT_LOGO_PATH = STATIC_ROOT / "images" / "logo.png"

# Logging — console only on Railway, file logging locally
_log_handlers: list[str] = ["console"]
_log_handler_config: dict[str, dict[str, Any]] = {
    "console": {
        "class": "logging.StreamHandler",
        "formatter": "verbose",
    },
}

if DEBUG and not _database_url:
    # Local dev: also log to file
    os.makedirs(BASE_DIR / "logs", exist_ok=True)
    _log_handlers.append("file")
    _log_handler_config["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(BASE_DIR / "logs" / "nis2_analyzer.log"),
        "maxBytes": 1024 * 1024 * 10,
        "backupCount": 5,
        "formatter": "verbose",
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{levelname} {asctime} {module} "
                "{process:d} {thread:d} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": _log_handler_config,
    "root": {
        "handlers": _log_handlers,
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": _log_handlers,
            "level": "INFO",
            "propagate": False,
        },
        "nis2_agents": {
            "handlers": _log_handlers,
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
