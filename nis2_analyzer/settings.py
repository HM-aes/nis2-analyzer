"""
Django settings for NIS2 Compliance Analyzer
"""

import os
import dj_database_url
from pathlib import Path
from decouple import config

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = config("SECRET_KEY", default="django-insecure-CHANGE-THIS-IN-PRODUCTION")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    # NIS2 Apps
    "compliance_engine",
    "nis2_agents",
    "rag_engine",
    "dashboard",
    "report_generator",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "nis2_analyzer.wsgi.application"

# Database — PostgreSQL on Railway (DATABASE_URL), SQLite locally
_database_url = config("DATABASE_URL", default="")
if _database_url:
    DATABASES = {"default": dj_database_url.parse(_database_url, conn_max_age=600)}
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
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "nl-NL"
TIME_ZONE = "Europe/Amsterdam"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth
LOGIN_URL = "/dashboard/login/"

# CORS Settings
CORS_ALLOWED_ORIGINS = config(
    "CORS_ORIGINS",
    default="http://localhost:3000,http://localhost:5173",
    cast=lambda v: [s.strip() for s in v.split(",")],
)
CORS_ALLOW_CREDENTIALS = True

# REST Framework
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
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
# Local on-disk mode for dev; None in production (uses QDRANT_HOST/PORT instead)
QDRANT_LOCAL_PATH = None if _database_url else BASE_DIR / "qdrant_local"

# AI API Keys
GOOGLE_API_KEY = config("GOOGLE_API_KEY", default="")

# Embedding Model (fastembed — BAAI/bge-small-en-v1.5 is 384-dim, same as all-MiniLM-L6-v2)
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# Document Processing
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_DOCUMENT_TYPES = [".pdf", ".docx", ".txt", ".md"]

# NIS2 Report Configuration
REPORT_TEMPLATES_DIR = BASE_DIR / "templates" / "reports"
REPORT_OUTPUT_DIR = MEDIA_ROOT / "reports"
REPORT_LOGO_PATH = STATIC_ROOT / "images" / "logo.png"

# Logging — console only on Railway, file logging locally
_log_handlers = ["console"]
_log_handler_config = {
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
        "filename": BASE_DIR / "logs" / "nis2_analyzer.log",
        "maxBytes": 1024 * 1024 * 10,
        "backupCount": 5,
        "formatter": "verbose",
    }

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
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
