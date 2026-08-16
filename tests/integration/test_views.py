import uuid

import pytest
from django.test import Client
from django.urls import reverse

from apps.playlist_sync.models import SyncJob
from providers.fakes import DEMO_PLAYLIST_URL


@pytest.mark.django_db
def test_login_required_for_sync(client):
    response = client.get(reverse("playlist_sync:sync_playlist"))
    assert response.status_code == 302
    assert reverse("accounts:login") in response.url


@pytest.mark.django_db
def test_csrf_rejected_on_logout(user):
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)
    response = client.post(reverse("accounts:logout"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_logout_with_csrf(user, client):
    client.force_login(user)
    response = client.post(reverse("accounts:logout"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_cross_user_job_is_404(client, user, other_user):
    job = SyncJob.objects.create(
        user=other_user,
        youtube_playlist_url=DEMO_PLAYLIST_URL,
        spotify_playlist_name="secret",
        idempotency_key="other-key",
    )
    client.force_login(user)
    response = client.get(reverse("playlist_sync:review", args=[job.pk]))
    assert response.status_code == 404
    response = client.get(reverse("playlist_sync:status", args=[job.pk]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_submit_creates_job_and_is_idempotent(client, user):
    client.force_login(user)
    key = uuid.uuid4().hex
    payload = {
        "youtube_playlist_url": DEMO_PLAYLIST_URL,
        "spotify_playlist_name": "Demo",
        "idempotency_key": key,
    }
    first = client.post(reverse("playlist_sync:sync_playlist"), payload)
    second = client.post(reverse("playlist_sync:sync_playlist"), payload)
    assert first.status_code == 302
    assert second.status_code == 302
    assert SyncJob.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_security_headers_and_httponly_cookies(settings):
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.CSRF_COOKIE_HTTPONLY is True
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings.X_FRAME_OPTIONS == "DENY"
