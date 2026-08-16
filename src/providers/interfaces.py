from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence


class YoutubeInputKind(str, Enum):
    PLAYLIST = "playlist"
    CHANNEL = "channel"


@dataclass(frozen=True)
class ParsedYoutubeInput:
    kind: YoutubeInputKind
    raw_url: str
    playlist_id: str | None = None
    channel_id: str | None = None
    handle: str | None = None
    custom_name: str | None = None
    user_name: str | None = None


@dataclass(frozen=True)
class YoutubeVideo:
    video_id: str
    title: str


@dataclass(frozen=True)
class SpotifyArtist:
    name: str


@dataclass(frozen=True)
class SpotifyTrack:
    track_id: str
    name: str
    artists: tuple[SpotifyArtist, ...]
    popularity: int = 0

    @property
    def primary_artist(self) -> str:
        return self.artists[0].name if self.artists else ""


@dataclass(frozen=True)
class SpotifyPlaylist:
    playlist_id: str
    name: str
    track_count: int = 0


@dataclass(frozen=True)
class ClassificationResult:
    classification: str
    artist: str | None
    song: str | None
    confidence: float
    prompt_version: str
    cached: bool = False
    tokens_used: int = 0
    latency_ms: float = 0.0
    model: str = ""
    estimated_cost_usd: float = 0.0
    skip_reason: str = ""


class YouTubeClient(Protocol):
    def resolve(self, url: str) -> ParsedYoutubeInput:
        """Parse and, if needed, resolve a channel URL to an uploads playlist."""

    def list_videos(self, parsed: ParsedYoutubeInput, *, limit: int) -> list[YoutubeVideo]:
        """Return playlist videos, honouring pagination and the caller's limit."""


class SpotifyClient(Protocol):
    def list_playlists(self) -> list[SpotifyPlaylist]:
        """Enumerate the current user's playlists with pagination."""

    def get_playlist(self, playlist_id: str) -> SpotifyPlaylist:
        """Fetch a single playlist the user can access."""

    def list_playlist_track_ids(self, playlist_id: str) -> list[str]:
        """Return all track IDs on a playlist, paginated."""

    def search_track(self, artist: str, song: str) -> SpotifyTrack | None:
        """Rank Spotify search results and return the best match, if any."""

    def create_playlist(self, name: str) -> str:
        """Create a private playlist and return its id."""

    def add_tracks(self, playlist_id: str, track_ids: Sequence[str]) -> None:
        """Append tracks in order. Callers must batch to 100 items."""

    def refresh_credentials(self) -> None:
        """Refresh an expired access token or raise SpotifyRevoked."""

    def disconnect(self) -> None:
        """Clear local credentials and attempt provider revocation."""


class SongClassifier(Protocol):
    def classify(self, video: YoutubeVideo) -> ClassificationResult:
        """Return a validated classification. Treat model output as untrusted."""
