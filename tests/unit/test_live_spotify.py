from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from django.utils import timezone
from requests import RequestException
from spotipy.exceptions import SpotifyException

from core.exceptions import BudgetExceeded, SpotifyPartialBatch, SpotifyRateLimited, SpotifyRevoked, SpotifyUnavailable
from providers import spotify as spotify_module
from providers.spotify import LiveSpotifyClient


@pytest.fixture
def live_client(monkeypatch):
    user = SimpleNamespace(
        spotify_access_token="access",
        spotify_refresh_token="refresh",
        spotify_token_expires_at=timezone.now() + timedelta(hours=1),
        spotify_connected=True,
        save=MagicMock(),
    )
    client = object.__new__(LiveSpotifyClient)
    client._user = user
    client._timeout = 5
    client._request_budget = 20
    client._requests_used = 0
    client._job_id = 1
    client._correlation_id = "corr"
    client._client = MagicMock()
    monkeypatch.setattr(spotify_module, "retry_with_jitter", lambda operation, attempts: operation())
    return client


def test_constructor_builds_sdk_client(monkeypatch):
    sdk_client = MagicMock()
    spotify = MagicMock(return_value=sdk_client)
    monkeypatch.setattr(spotify_module.spotipy, "Spotify", spotify)
    user = SimpleNamespace(spotify_access_token="token")

    client = LiveSpotifyClient(user, timeout=3, request_budget=4)

    assert client._client is sdk_client
    assert client._request_budget == 4
    spotify.assert_called_once_with(auth="token", requests_timeout=3, retries=0)


def test_constructor_requires_access_token():
    with pytest.raises(SpotifyRevoked):
        LiveSpotifyClient(SimpleNamespace(spotify_access_token=""), timeout=3, request_budget=4)


def test_refresh_credentials_skips_fresh_token(live_client):
    original = live_client._client
    live_client.refresh_credentials()
    assert live_client._client is original


def test_refresh_credentials_updates_user(monkeypatch, live_client):
    live_client._user.spotify_token_expires_at = timezone.now() - timedelta(seconds=1)
    oauth = MagicMock()
    oauth.refresh_access_token.return_value = {
        "access_token": "new-access",
        "refresh_token": "new-refresh",
        "expires_in": 120,
    }
    monkeypatch.setattr(spotify_module, "SpotifyOAuth", MagicMock(return_value=oauth))
    rebuilt = MagicMock()
    monkeypatch.setattr(live_client, "_build_client", MagicMock(return_value=rebuilt))

    live_client.refresh_credentials()

    assert live_client._user.spotify_access_token == "new-access"
    assert live_client._user.spotify_refresh_token == "new-refresh"
    assert live_client._user.spotify_connected is True
    assert live_client._client is rebuilt
    live_client._user.save.assert_called_once()


def test_refresh_credentials_maps_missing_or_failed_refresh(monkeypatch, live_client):
    live_client._user.spotify_refresh_token = ""
    with pytest.raises(SpotifyRevoked):
        live_client.refresh_credentials()

    live_client._user.spotify_refresh_token = "refresh"
    live_client._user.spotify_token_expires_at = None
    oauth = MagicMock()
    oauth.refresh_access_token.side_effect = RuntimeError("provider failed")
    monkeypatch.setattr(spotify_module, "SpotifyOAuth", MagicMock(return_value=oauth))
    with pytest.raises(SpotifyRevoked):
        live_client.refresh_credentials()


def test_disconnect_revokes_and_clears_credentials(monkeypatch, live_client):
    post = MagicMock()
    monkeypatch.setattr(spotify_module.requests, "post", post)

    live_client.disconnect()

    post.assert_called_once()
    assert live_client._user.spotify_access_token == ""
    assert live_client._user.spotify_refresh_token == ""
    assert live_client._user.spotify_token_expires_at is None
    assert live_client._user.spotify_connected is False


def test_disconnect_still_clears_after_network_failure(monkeypatch, live_client):
    monkeypatch.setattr(spotify_module.requests, "post", MagicMock(side_effect=RequestException("offline")))
    live_client.disconnect()
    assert live_client._user.spotify_connected is False


def test_playlist_reads_are_paginated(live_client):
    live_client._client.current_user_playlists.side_effect = [
        {"items": [{"id": "p1", "name": "One", "tracks": {"total": 2}}], "next": "next"},
        {"items": [{"id": "p2", "name": "Two", "tracks": {"total": 0}}], "next": None},
    ]
    live_client._client.playlist.return_value = {"id": "p1", "name": "One", "tracks": {"total": 2}}

    playlists = live_client.list_playlists()
    playlist = live_client.get_playlist("p1")

    assert [item.playlist_id for item in playlists] == ["p1", "p2"]
    assert playlist.name == "One"
    assert playlist.track_count == 2


def test_playlist_track_ids_skip_missing_tracks(live_client):
    live_client._client.playlist_items.side_effect = [
        {"items": [{"track": {"id": "t1"}}, {"track": None}], "next": "next"},
        {"items": [{"track": {"id": "t2"}}, {}], "next": None},
    ]
    assert live_client.list_playlist_track_ids("p1") == ["t1", "t2"]


def test_search_ranks_results_and_rejects_weak_match(live_client):
    live_client._client.search.return_value = {
        "tracks": {
            "items": [
                {"id": "weak", "name": "Other", "artists": [{"name": "Nobody"}], "popularity": 99},
                {"id": "best", "name": "Hello", "artists": [{"name": "Adele"}], "popularity": 1},
            ]
        }
    }
    assert live_client.search_track("Adele", "Hello").track_id == "best"

    live_client._client.search.return_value = {"tracks": {"items": []}}
    assert live_client.search_track("Adele", "Hello") is None

    live_client._client.search.return_value = {
        "tracks": {"items": [{"id": "x", "name": "Other", "artists": [], "popularity": 0}]}
    }
    assert live_client.search_track("Adele", "Hello") is None


def test_create_and_add_tracks(live_client):
    live_client._client.current_user.return_value = {"id": "me"}
    live_client._client.user_playlist_create.return_value = {"id": "new"}
    assert live_client.create_playlist("Mix") == "new"

    live_client.add_tracks("new", [])
    live_client._client.playlist_add_items.assert_not_called()
    live_client.add_tracks("new", ["t1", "t2"])
    live_client._client.playlist_add_items.assert_called_once_with("new", ["t1", "t2"])
    with pytest.raises(SpotifyPartialBatch):
        live_client.add_tracks("new", [str(index) for index in range(101)])


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, SpotifyRevoked),
        (403, SpotifyRevoked),
        (429, SpotifyRateLimited),
        (500, SpotifyUnavailable),
        (418, SpotifyUnavailable),
    ],
)
def test_call_maps_spotify_errors(status, expected, live_client):
    error = SpotifyException(status, -1, "failure", headers={"X-Request-Id": "request-1"})
    with pytest.raises(expected) as caught:
        live_client._call(MagicMock(side_effect=error))
    assert caught.value.request_id == "request-1"


def test_call_enforces_request_budget(live_client):
    live_client._requests_used = live_client._request_budget
    with pytest.raises(BudgetExceeded):
        live_client._call(MagicMock())


def test_add_tracks_preserves_mapped_errors_and_wraps_unknown(live_client):
    monkey = MagicMock(side_effect=SpotifyRateLimited())
    live_client._call = monkey
    with pytest.raises(SpotifyRateLimited):
        live_client.add_tracks("p1", ["t1"])

    live_client._call = MagicMock(side_effect=SpotifyRevoked())
    with pytest.raises(SpotifyRevoked):
        live_client.add_tracks("p1", ["t1"])

    live_client._call = MagicMock(side_effect=RuntimeError("unknown"))
    with pytest.raises(SpotifyPartialBatch):
        live_client.add_tracks("p1", ["t1"])
