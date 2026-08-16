import os
import sys
from pathlib import Path

import dj_database_url

from providers.spotify import SPOTIFY_SCOPES
from sync.config import get_settings

BASE_DIR = Path(__file__).resolve().parent.parent
app = get_settings()

SECRET_KEY = app.django_secret_key
DEBUG = app.debug
TESTING = app.testing or "pytest" in sys.modules or os.getenv("SYNC_TESTING") == "1"

ALLOWED_HOSTS = app.allowed_hosts_list
CSRF_TRUSTED_ORIGINS = app.csrf_trusted_origins_list
TOKEN_ENCRYPTION_KEY = app.token_encryption_key

SYNC_PROVIDER_MODE = app.provider_mode if not TESTING else os.getenv("SYNC_PROVIDER_MODE", "fake")
SYNC_MAX_PLAYLIST_SIZE = app.max_playlist_size
SYNC_JOB_TIMEOUT_SECONDS = app.job_timeout_seconds
SYNC_YOUTUBE_REQUEST_BUDGET = app.youtube_request_budget
SYNC_SPOTIFY_REQUEST_BUDGET = app.spotify_request_budget
SYNC_AI_COST_BUDGET_USD = app.ai_cost_budget_usd
SYNC_YOUTUBE_TIMEOUT_SECONDS = app.youtube_timeout_seconds
SYNC_SPOTIFY_TIMEOUT_SECONDS = app.spotify_timeout_seconds
SYNC_AI_TIMEOUT_SECONDS = app.ai_timeout_seconds
SYNC_AI_MODEL = app.ai_model
SYNC_CONFIDENCE_THRESHOLD = app.confidence_threshold
SYNC_CLASSIFICATION_CACHE_DAYS = app.classification_cache_days

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crispy_forms",
    "crispy_bootstrap5",
    "social_django",
    "apps.accounts",
    "apps.dashboard",
    "apps.playlist_sync",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "sync.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "sync.wsgi.application"

if TESTING:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
elif app.database_url:
    DATABASES = {"default": dj_database_url.parse(app.database_url, conn_max_age=600)}
else:
    DATABASES = {
        "default": {
            "ENGINE": app.sql_engine,
            "NAME": app.postgres_db,
            "USER": app.postgres_user,
            "PASSWORD": app.postgres_password,
            "HOST": app.postgres_host,
            "PORT": app.postgres_port,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

AUTHENTICATION_BACKENDS = (
    "social_core.backends.spotify.SpotifyOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)

SOCIAL_AUTH_SPOTIFY_KEY = app.spotify_client_id
SOCIAL_AUTH_SPOTIFY_SECRET = app.spotify_client_secret
SOCIAL_AUTH_SPOTIFY_SCOPE = list(SPOTIFY_SCOPES)
SOCIAL_AUTH_SPOTIFY_REDIRECT_URI = app.spotify_redirect_uri
SOCIAL_AUTH_REDIRECT_IS_HTTPS = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

SOCIAL_AUTH_URL_NAMESPACE = "social"
SOCIAL_AUTH_LOGIN_REDIRECT_URL = "dashboard:dashboard"
SOCIAL_AUTH_LOGIN_ERROR_URL = "accounts:login"
SOCIAL_AUTH_RAISE_EXCEPTIONS = False
SOCIAL_AUTH_SPOTIFY_AUTH_EXTRA_ARGUMENTS = {"show_dialog": True}

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "apps.accounts.pipeline.save_spotify_tokens",
)

YOUTUBE_API_KEY = app.youtube_api_key
OPENAI_API_KEY = app.openai_api_key

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": app.log_level,
    },
    "loggers": {
        "django.security": {"handlers": ["console"], "level": app.log_level, "propagate": False},
        "apps": {"handlers": ["console"], "level": app.log_level, "propagate": False},
        "providers": {"handlers": ["console"], "level": app.log_level, "propagate": False},
        "celery": {"handlers": ["console"], "level": app.log_level, "propagate": False},
    },
}

REDIS_URL = f"redis://{app.redis_host}:{app.redis_port}"
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"amqp://guest:guest@{app.rabbitmq_host}:5672//")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_ALWAYS_EAGER = TESTING
CELERY_TASK_EAGER_PROPAGATES = TESTING
