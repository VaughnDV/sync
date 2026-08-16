from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from core.exceptions import YoutubeInvalidUrl
from providers.interfaces import ParsedYoutubeInput, YoutubeInputKind

_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def parse_youtube_url(url: str) -> ParsedYoutubeInput:
    """Parse supported YouTube playlist and channel URLs without network access."""
    if not url or not url.strip():
        raise YoutubeInvalidUrl()

    raw = url.strip()
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = (parsed.hostname or "").lower()
    if host not in _YOUTUBE_HOSTS:
        raise YoutubeInvalidUrl()

    path = parsed.path or ""
    query = parse_qs(parsed.query)
    playlist_id = _first(query.get("list"))

    if playlist_id and _valid_playlist_id(playlist_id):
        return ParsedYoutubeInput(
            kind=YoutubeInputKind.PLAYLIST,
            raw_url=raw,
            playlist_id=playlist_id,
        )

    if host == "youtu.be":
        raise YoutubeInvalidUrl()

    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        raise YoutubeInvalidUrl()

    if segments[0] == "playlist":
        raise YoutubeInvalidUrl()

    if segments[0] == "channel" and len(segments) >= 2:
        return ParsedYoutubeInput(
            kind=YoutubeInputKind.CHANNEL,
            raw_url=raw,
            channel_id=segments[1],
        )

    if segments[0] == "c" and len(segments) >= 2:
        return ParsedYoutubeInput(
            kind=YoutubeInputKind.CHANNEL,
            raw_url=raw,
            custom_name=segments[1],
        )

    if segments[0] == "user" and len(segments) >= 2:
        return ParsedYoutubeInput(
            kind=YoutubeInputKind.CHANNEL,
            raw_url=raw,
            user_name=segments[1],
        )

    if segments[0].startswith("@") and len(segments[0]) > 1:
        return ParsedYoutubeInput(
            kind=YoutubeInputKind.CHANNEL,
            raw_url=raw,
            handle=segments[0][1:],
        )

    raise YoutubeInvalidUrl()


def _first(values: list[str] | None) -> str | None:
    if not values:
        return None
    return values[0]


def _valid_playlist_id(playlist_id: str) -> bool:
    return playlist_id.startswith(("PL", "UU", "LL", "FL", "OL")) and len(playlist_id) >= 10
