import os

os.environ.setdefault("SYNC_TESTING", "1")
os.environ.setdefault("SYNC_PROVIDER_MODE", "fake")
os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,testserver")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

import pytest

from providers.factory import reset_fakes
from providers.fakes import (
    DEMO_PLAYLIST_URL,
    FakeSongClassifier,
    FakeSpotifyClient,
    FakeYouTubeClient,
)


def pytest_configure():
    os.environ["DJANGO_SETTINGS_MODULE"] = "tests.settings"
    os.environ["SYNC_TESTING"] = "1"


@pytest.fixture(autouse=True)
def _eager_celery(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    from sync.celery import app

    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True


@pytest.fixture(autouse=True)
def _reset_provider_fakes():
    reset_fakes()
    yield
    reset_fakes()


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model

    account = get_user_model().objects.create_user(email="demo@example.com", username="demo", password="password123")
    account.spotify_connected = True
    account.spotify_access_token = "access-token"
    account.spotify_refresh_token = "refresh-token"
    account.save()
    return account


@pytest.fixture
def other_user(db):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(email="other@example.com", username="other", password="password123")


@pytest.fixture
def job(user):
    from apps.playlist_sync.models import SyncJob

    return SyncJob.objects.create(
        user=user,
        youtube_playlist_url=DEMO_PLAYLIST_URL,
        spotify_playlist_name="Demo playlist",
        idempotency_key="key-1",
    )


@pytest.fixture
def youtube():
    return FakeYouTubeClient()


@pytest.fixture
def spotify():
    return FakeSpotifyClient()


@pytest.fixture
def classifier():
    return FakeSongClassifier()
