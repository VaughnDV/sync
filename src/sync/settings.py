import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-default-key-for-development')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'rpi.vaughndv.com']

# CSRF Settings
CSRF_TRUSTED_ORIGINS = ['https://rpi.vaughndv.com']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'social_django',
    'apps.accounts',
    'apps.dashboard',
    'apps.playlist_sync',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sync.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sync.wsgi.application'

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgres://postgres:postgres@db:5432/vaughndv')
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL)
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'src/static')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Social Auth
AUTHENTICATION_BACKENDS = (
    'social_core.backends.spotify.SpotifyOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_SPOTIFY_KEY = os.getenv('SPOTIFY_CLIENT_ID')
SOCIAL_AUTH_SPOTIFY_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SOCIAL_AUTH_SPOTIFY_SCOPE = ['playlist-read-private', 'playlist-modify-public', 'playlist-modify-private']
SOCIAL_AUTH_SPOTIFY_REDIRECT_URI = 'https://rpi.vaughndv.com/social-auth/complete/spotify/'
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True    
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Social Auth settings
SOCIAL_AUTH_URL_NAMESPACE = 'social'
SOCIAL_AUTH_LOGIN_REDIRECT_URL = 'dashboard:dashboard'
SOCIAL_AUTH_LOGIN_ERROR_URL = 'accounts:login'
SOCIAL_AUTH_RAISE_EXCEPTIONS = True
SOCIAL_AUTH_SPOTIFY_AUTH_EXTRA_ARGUMENTS = {'show_dialog': True}

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'apps.accounts.pipeline.save_spotify_tokens',
)

# API Keys
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Debug settings
SOCIAL_AUTH_LOGIN_ERROR_URL = 'accounts:login'
SOCIAL_AUTH_RAISE_EXCEPTIONS = True
SOCIAL_AUTH_SPOTIFY_AUTH_EXTRA_ARGUMENTS = {'show_dialog': True}

# Add logging for social auth
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'social_core': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'apps.playlist_sync.services': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Set to INFO in production
        },
    },
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Add logging for Celery
LOGGING['loggers'].update({
    'celery': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'celery.task': {
        'handlers': ['console'],
        'level': 'DEBUG',
    }
}) 