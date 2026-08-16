from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from datetime import timedelta

import requests
import spotipy
from django.conf import settings
from django.utils import timezone
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyOAuth

from core.exceptions import (
    BudgetExceeded,
    SpotifyPartialBatch,
    SpotifyRateLimited,
    SpotifyRevoked,
    SpotifyUnavailable,
)
from core.logging import job_log
from core.retry import retry_with_jitter
from providers.interfaces import SpotifyArtist, SpotifyPlaylist, SpotifyTrack

logger = logging.getLogger(__name__)

SPOTIFY_SCOPES = ("playlist-read-private", "playlist-modify-private")
SEARCH_LIMIT = 5


class LiveSpotifyClient:
    def __init__(
        self,
        user: object,
        *,
        timeout: int | None = None,
        request_budget: int | None = None,
        job_id: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self._user = user
        self._timeout = timeout or settings.SYNC_SPOTIFY_TIMEOUT_SECONDS
        self._request_budget = request_budget or settings.SYNC_SPOTIFY_REQUEST_BUDGET
        self._requests_used = 0
        self._job_id = job_id
        self._correlation_id = correlation_id
        self._client = self._build_client()

    def refresh_credentials(self) -> None:
        expires_at = getattr(self._user, "spotify_token_expires_at", None)
        refresh_token = getattr(self._user, "spotify_refresh_token", None)
        if not refresh_token:
            raise SpotifyRevoked()
        if expires_at and expires_at > timezone.now() + timedelta(seconds=60):
            return
        oauth = SpotifyOAuth(
            client_id=settings.SOCIAL_AUTH_SPOTIFY_KEY,
            client_secret=settings.SOCIAL_AUTH_SPOTIFY_SECRET,
            redirect_uri=settings.SOCIAL_AUTH_SPOTIFY_REDIRECT_URI,
            scope=" ".join(SPOTIFY_SCOPES),
            requests_timeout=self._timeout,
        )
        try:
            token_info = oauth.refresh_access_token(refresh_token)
        except Exception as exc:  # noqa: BLE001 - map any SDK/auth failure
            raise SpotifyRevoked() from exc
        self._user.spotify_access_token = token_info.get("access_token") or ""
        if token_info.get("refresh_token"):
            self._user.spotify_refresh_token = token_info["refresh_token"]
        expires_in = int(token_info.get("expires_in") or 3600)
        self._user.spotify_token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        self._user.spotify_connected = True
        self._user.save(
            update_fields=[
                "spotify_access_token",
                "spotify_refresh_token",
                "spotify_token_expires_at",
                "spotify_connected",
            ]
        )
        self._client = self._build_client()

    def disconnect(self) -> None:
        token = getattr(self._user, "spotify_access_token", None)
        if token:
            try:
                requests.post(
                    "https://accounts.spotify.com/api/token",
                    data={"token": token, "token_type_hint": "access_token"},
                    auth=(settings.SOCIAL_AUTH_SPOTIFY_KEY, settings.SOCIAL_AUTH_SPOTIFY_SECRET),
                    timeout=self._timeout,
                )
            except requests.RequestException:
                logger.info("spotify.revoke_failed", extra={"sync": {"provider": "spotify"}})
        self._user.spotify_access_token = ""
        self._user.spotify_refresh_token = ""
        self._user.spotify_token_expires_at = None
        self._user.spotify_connected = False
        self._user.save(
            update_fields=[
                "spotify_access_token",
                "spotify_refresh_token",
                "spotify_token_expires_at",
                "spotify_connected",
            ]
        )

    def list_playlists(self) -> list[SpotifyPlaylist]:
        playlists: list[SpotifyPlaylist] = []
        offset = 0
        while True:
            current_offset = offset
            payload = self._call(
                lambda current_offset=current_offset: self._client.current_user_playlists(
                    limit=50, offset=current_offset
                )
            )
            for item in payload.get("items") or []:
                playlists.append(
                    SpotifyPlaylist(
                        playlist_id=item["id"],
                        name=item.get("name") or "",
                        track_count=(item.get("tracks") or {}).get("total") or 0,
                    )
                )
            offset += len(payload.get("items") or [])
            if not payload.get("next"):
                break
        return playlists

    def get_playlist(self, playlist_id: str) -> SpotifyPlaylist:
        payload = self._call(lambda: self._client.playlist(playlist_id, fields="id,name,tracks.total"))
        return SpotifyPlaylist(
            playlist_id=payload["id"],
            name=payload.get("name") or "",
            track_count=(payload.get("tracks") or {}).get("total") or 0,
        )

    def list_playlist_track_ids(self, playlist_id: str) -> list[str]:
        track_ids: list[str] = []
        offset = 0
        while True:
            current_offset = offset
            payload = self._call(
                lambda current_offset=current_offset: self._client.playlist_items(
                    playlist_id,
                    fields="items(track(id)),next",
                    limit=100,
                    offset=current_offset,
                )
            )
            for item in payload.get("items") or []:
                track = item.get("track") or {}
                track_id = track.get("id")
                if track_id:
                    track_ids.append(track_id)
            offset += len(payload.get("items") or [])
            if not payload.get("next"):
                break
        return track_ids

    def search_track(self, artist: str, song: str) -> SpotifyTrack | None:
        query = f"artist:{artist} track:{song}"
        payload = self._call(lambda: self._client.search(q=query, type="track", limit=SEARCH_LIMIT))
        items = ((payload.get("tracks") or {}).get("items")) or []
        ranked = sorted(
            (self._to_track(item) for item in items),
            key=lambda track: self._score(track, artist, song),
            reverse=True,
        )
        if not ranked:
            return None
        best = ranked[0]
        if self._score(best, artist, song) < 1:
            return None
        return best

    def create_playlist(self, name: str) -> str:
        me = self._call(lambda: self._client.current_user())
        payload = self._call(
            lambda: self._client.user_playlist_create(me["id"], name, public=False, description="Created by Sync")
        )
        return payload["id"]

    def add_tracks(self, playlist_id: str, track_ids: Sequence[str]) -> None:
        if not track_ids:
            return
        if len(track_ids) > 100:
            raise SpotifyPartialBatch()
        try:
            self._call(lambda: self._client.playlist_add_items(playlist_id, list(track_ids)))
        except SpotifyRateLimited:
            raise
        except SpotifyRevoked:
            raise
        except Exception as exc:  # noqa: BLE001
            raise SpotifyPartialBatch() from exc

    def _build_client(self) -> spotipy.Spotify:
        token = getattr(self._user, "spotify_access_token", None)
        if not token:
            raise SpotifyRevoked()
        return spotipy.Spotify(auth=token, requests_timeout=self._timeout, retries=0)

    def _call(self, operation):
        self.refresh_credentials()
        if self._requests_used >= self._request_budget:
            raise BudgetExceeded()
        self._requests_used += 1
        started = time.perf_counter()

        def _wrapped():
            try:
                return operation()
            except SpotifyException as exc:
                request_id = ""
                headers = getattr(exc, "headers", None) or {}
                request_id = headers.get("x-request-id") or headers.get("X-Request-Id") or ""
                if exc.http_status in {401, 403}:
                    raise SpotifyRevoked(request_id=request_id) from exc
                if exc.http_status == 429:
                    raise SpotifyRateLimited(request_id=request_id) from exc
                if exc.http_status in {500, 502, 503, 504}:
                    raise SpotifyUnavailable(request_id=request_id) from exc
                raise SpotifyUnavailable(request_id=request_id) from exc

        result = retry_with_jitter(_wrapped, attempts=3)
        job_log(
            logger,
            "spotify.request",
            job_id=self._job_id,
            provider="spotify",
            stage="request",
            duration_ms=round((time.perf_counter() - started) * 1000, 1),
            correlation_id=self._correlation_id,
        )
        return result

    def _to_track(self, item: dict) -> SpotifyTrack:
        artists = tuple(SpotifyArtist(name=artist.get("name") or "") for artist in item.get("artists") or [])
        return SpotifyTrack(
            track_id=item["id"],
            name=item.get("name") or "",
            artists=artists,
            popularity=int(item.get("popularity") or 0),
        )

    def _score(self, track: SpotifyTrack, artist: str, song: str) -> int:
        score = 0
        if track.name.lower() == song.lower():
            score += 4
        elif song.lower() in track.name.lower():
            score += 2
        artist_names = {item.name.lower() for item in track.artists}
        if artist.lower() in artist_names:
            score += 4
        elif any(artist.lower() in name for name in artist_names):
            score += 2
        if track.popularity:
            score += 1
        return score
