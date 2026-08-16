from __future__ import annotations

from django.conf import settings

from providers.classifier import LiveSongClassifier
from providers.fakes import FakeSongClassifier, FakeSpotifyClient, FakeYouTubeClient
from providers.interfaces import SongClassifier, SpotifyClient, YouTubeClient
from providers.spotify import LiveSpotifyClient
from providers.youtube import LiveYouTubeClient

_fake_spotify: FakeSpotifyClient | None = None
_fake_classifier: FakeSongClassifier | None = None


def get_youtube_client(*, job_id: int | None = None, correlation_id: str | None = None) -> YouTubeClient:
    if settings.SYNC_PROVIDER_MODE == "fake":
        return FakeYouTubeClient()
    return LiveYouTubeClient(job_id=job_id, correlation_id=correlation_id)


def get_spotify_client(
    user: object,
    *,
    job_id: int | None = None,
    correlation_id: str | None = None,
) -> SpotifyClient:
    global _fake_spotify
    if settings.SYNC_PROVIDER_MODE == "fake":
        if _fake_spotify is None:
            _fake_spotify = FakeSpotifyClient(user=user)
        else:
            _fake_spotify._user = user
        return _fake_spotify
    return LiveSpotifyClient(user, job_id=job_id, correlation_id=correlation_id)


def get_classifier(
    *,
    job_id: int | None = None,
    correlation_id: str | None = None,
    cache_model: object | None = None,
) -> SongClassifier:
    global _fake_classifier
    if settings.SYNC_PROVIDER_MODE == "fake":
        if _fake_classifier is None:
            _fake_classifier = FakeSongClassifier()
        return _fake_classifier
    return LiveSongClassifier(
        job_id=job_id,
        correlation_id=correlation_id,
        cache_model=cache_model,
    )


def reset_fakes() -> None:
    global _fake_spotify, _fake_classifier
    _fake_spotify = None
    _fake_classifier = None
