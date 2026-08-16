from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy

from core.exceptions import (
    AIInvalidSchema,
    AIRateLimited,
    AIRefusal,
    AITimeout,
    BudgetExceeded,
    JobCancelled,
    SpotifyPartialBatch,
    SpotifyRateLimited,
    SpotifyRevoked,
    YoutubePaginationFailed,
    YoutubeQuotaExceeded,
)
from providers.interfaces import (
    ClassificationResult,
    ParsedYoutubeInput,
    SpotifyArtist,
    SpotifyPlaylist,
    SpotifyTrack,
    YoutubeVideo,
)
from providers.schemas import PROMPT_VERSION, SongClassification
from providers.youtube_urls import parse_youtube_url

DEMO_PLAYLIST_ID = "PLdemodemo01"
DEMO_PLAYLIST_URL = f"https://www.youtube.com/playlist?list={DEMO_PLAYLIST_ID}"

DEMO_VIDEOS: tuple[YoutubeVideo, ...] = (
    YoutubeVideo(video_id="vidHello01", title="Adele - Hello (Official Video)"),
    YoutubeVideo(video_id="vidWonder1", title="Wonderwall cover by a street musician"),
    YoutubeVideo(video_id="vidPython1", title="Python tutorial for beginners"),
    YoutubeVideo(video_id="vidMaybe01", title="maybe this is a song??? live clip"),
    YoutubeVideo(video_id="vidCreep01", title="Radiohead - Creep"),
)

DEMO_CLASSIFICATIONS: dict[str, SongClassification] = {
    "vidHello01": SongClassification(classification="music", artist="Adele", song="Hello", confidence=0.96),
    "vidWonder1": SongClassification(classification="music", artist="Oasis", song="Wonderwall", confidence=0.91),
    "vidPython1": SongClassification(classification="not_music", artist=None, song=None, confidence=0.99),
    "vidMaybe01": SongClassification(classification="uncertain", artist=None, song=None, confidence=0.41),
    "vidCreep01": SongClassification(classification="music", artist="Radiohead", song="Creep", confidence=0.94),
}

DEMO_CATALOG: tuple[SpotifyTrack, ...] = (
    SpotifyTrack(
        track_id="spHello01",
        name="Hello",
        artists=(SpotifyArtist(name="Adele"),),
        popularity=90,
    ),
    SpotifyTrack(
        track_id="spWonder1",
        name="Wonderwall",
        artists=(SpotifyArtist(name="Oasis"),),
        popularity=88,
    ),
    SpotifyTrack(
        track_id="spCreep01",
        name="Creep",
        artists=(SpotifyArtist(name="Radiohead"),),
        popularity=92,
    ),
)


class FakeYouTubeClient:
    def __init__(
        self,
        videos: Sequence[YoutubeVideo] | None = None,
        *,
        fail_after_pages: int | None = None,
        quota_exhausted: bool = False,
    ) -> None:
        self._videos = list(videos or DEMO_VIDEOS)
        self._fail_after_pages = fail_after_pages
        self._quota_exhausted = quota_exhausted
        self.requests = 0

    def resolve(self, url: str) -> ParsedYoutubeInput:
        parsed = parse_youtube_url(url)
        if parsed.kind.value == "channel":
            return ParsedYoutubeInput(
                kind=parsed.kind,
                raw_url=parsed.raw_url,
                playlist_id=DEMO_PLAYLIST_ID,
                channel_id=parsed.channel_id or "UCdemo",
                handle=parsed.handle,
                custom_name=parsed.custom_name,
                user_name=parsed.user_name,
            )
        return parsed

    def list_videos(self, parsed: ParsedYoutubeInput, *, limit: int) -> list[YoutubeVideo]:
        self.requests += 1
        if self._quota_exhausted:
            raise YoutubeQuotaExceeded()
        if self._fail_after_pages == 0:
            raise YoutubePaginationFailed()
        return list(self._videos[:limit])


class FakeSpotifyClient:
    def __init__(
        self,
        *,
        catalog: Sequence[SpotifyTrack] | None = None,
        playlists: dict[str, dict] | None = None,
        revoked: bool = False,
        rate_limited: bool = False,
        fail_batch_at: int | None = None,
        user: object | None = None,
    ) -> None:
        self._catalog = list(catalog or DEMO_CATALOG)
        self._playlists = playlists if playlists is not None else {}
        self._revoked = revoked
        self._rate_limited = rate_limited
        self._fail_batch_at = fail_batch_at
        self._user = user
        self.requests = 0
        self.created_playlists: list[str] = []
        self.added_batches: list[list[str]] = []

    def list_playlists(self) -> list[SpotifyPlaylist]:
        self._guard()
        return [
            SpotifyPlaylist(playlist_id=pid, name=data["name"], track_count=len(data["tracks"]))
            for pid, data in self._playlists.items()
        ]

    def get_playlist(self, playlist_id: str) -> SpotifyPlaylist:
        self._guard()
        data = self._playlists[playlist_id]
        return SpotifyPlaylist(playlist_id=playlist_id, name=data["name"], track_count=len(data["tracks"]))

    def list_playlist_track_ids(self, playlist_id: str) -> list[str]:
        self._guard()
        return list(self._playlists.get(playlist_id, {"tracks": []})["tracks"])

    def search_track(self, artist: str, song: str) -> SpotifyTrack | None:
        self._guard()
        artist_l, song_l = artist.lower(), song.lower()
        for track in self._catalog:
            if track.name.lower() == song_l and any(item.name.lower() == artist_l for item in track.artists):
                return track
        return None

    def create_playlist(self, name: str) -> str:
        self._guard()
        playlist_id = f"pl{len(self._playlists) + 1:06d}"
        self._playlists[playlist_id] = {"name": name, "tracks": []}
        self.created_playlists.append(playlist_id)
        return playlist_id

    def add_tracks(self, playlist_id: str, track_ids: Sequence[str]) -> None:
        self._guard()
        if self._fail_batch_at is not None and len(self.added_batches) >= self._fail_batch_at:
            raise SpotifyPartialBatch()
        self._playlists.setdefault(playlist_id, {"name": "Untitled", "tracks": []})
        self._playlists[playlist_id]["tracks"].extend(track_ids)
        self.added_batches.append(list(track_ids))

    def refresh_credentials(self) -> None:
        if self._revoked:
            raise SpotifyRevoked()

    def disconnect(self) -> None:
        if self._user is not None:
            self._user.spotify_access_token = ""
            self._user.spotify_refresh_token = ""
            self._user.spotify_connected = False

    def _guard(self) -> None:
        self.requests += 1
        if self._revoked:
            raise SpotifyRevoked()
        if self._rate_limited:
            raise SpotifyRateLimited()


class FakeSongClassifier:
    def __init__(
        self,
        results: dict[str, SongClassification] | None = None,
        *,
        malformed_ids: Sequence[str] = (),
        timeout_ids: Sequence[str] = (),
        refusal_ids: Sequence[str] = (),
        rate_limit: bool = False,
        cache: dict[str, ClassificationResult] | None = None,
        on_classify: Callable[[YoutubeVideo], None] | None = None,
    ) -> None:
        self._results = deepcopy(results or DEMO_CLASSIFICATIONS)
        self._malformed = set(malformed_ids)
        self._timeouts = set(timeout_ids)
        self._refusals = set(refusal_ids)
        self._rate_limit = rate_limit
        self._cache = cache if cache is not None else {}
        self.calls: list[str] = []
        self._on_classify = on_classify

    def classify(self, video: YoutubeVideo) -> ClassificationResult:
        if video.video_id in self._cache:
            cached = self._cache[video.video_id]
            return ClassificationResult(**{**cached.__dict__, "cached": True})
        self.calls.append(video.video_id)
        if self._on_classify:
            self._on_classify(video)
        if self._rate_limit:
            raise AIRateLimited()
        if video.video_id in self._timeouts:
            raise AITimeout()
        if video.video_id in self._refusals:
            raise AIRefusal()
        if video.video_id in self._malformed:
            raise AIInvalidSchema()
        parsed = self._results.get(video.video_id)
        if parsed is None:
            parsed = SongClassification(classification="uncertain", artist=None, song=None, confidence=0.2)
        result = ClassificationResult(
            classification=parsed.classification.value,
            artist=parsed.artist,
            song=parsed.song,
            confidence=parsed.confidence,
            prompt_version=PROMPT_VERSION,
            cached=False,
            tokens_used=42,
            latency_ms=1.0,
            model="fixture",
            estimated_cost_usd=0.0001,
        )
        self._cache[video.video_id] = result
        return result


def raise_if_cancelled(flag: bool) -> None:
    if flag:
        raise JobCancelled()


def raise_if_budget(spent: float, budget: float) -> None:
    if spent >= budget:
        raise BudgetExceeded()
