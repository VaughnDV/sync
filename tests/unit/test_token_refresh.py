from datetime import timedelta

import pytest
from django.utils import timezone

from core.exceptions import SpotifyRevoked
from providers.fakes import FakeSpotifyClient


@pytest.mark.django_db
def test_revoked_refresh_raises(user):
    user.spotify_token_expires_at = timezone.now() - timedelta(seconds=10)
    user.save()
    client = FakeSpotifyClient(user=user, revoked=True)
    with pytest.raises(SpotifyRevoked):
        client.refresh_credentials()


@pytest.mark.django_db
def test_disconnect_clears_local_tokens(user):
    client = FakeSpotifyClient(user=user)
    client.disconnect()
    assert user.spotify_connected is False
    assert user.spotify_access_token == ""
