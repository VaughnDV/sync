from __future__ import annotations

import logging
import time
from typing import Any

import httplib2
from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.exceptions import (
    BudgetExceeded,
    YoutubeNotFound,
    YoutubePaginationFailed,
    YoutubeQuotaExceeded,
)
from core.logging import job_log
from core.retry import retry_with_jitter
from providers.interfaces import ParsedYoutubeInput, YoutubeInputKind, YoutubeVideo
from providers.youtube_urls import parse_youtube_url

logger = logging.getLogger(__name__)


class LiveYouTubeClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: int | None = None,
        request_budget: int | None = None,
        job_id: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.YOUTUBE_API_KEY
        self._timeout = timeout or settings.SYNC_YOUTUBE_TIMEOUT_SECONDS
        self._request_budget = request_budget or settings.SYNC_YOUTUBE_REQUEST_BUDGET
        self._requests_used = 0
        self._job_id = job_id
        self._correlation_id = correlation_id
        http = httplib2.Http(timeout=self._timeout)
        self._client = build(
            "youtube",
            "v3",
            developerKey=self._api_key,
            http=http,
            cache_discovery=False,
        )

    def resolve(self, url: str) -> ParsedYoutubeInput:
        parsed = parse_youtube_url(url)
        if parsed.kind is YoutubeInputKind.PLAYLIST:
            return parsed
        channel_id = parsed.channel_id or self._lookup_channel_id(parsed)
        uploads_id = self._uploads_playlist(channel_id)
        return ParsedYoutubeInput(
            kind=YoutubeInputKind.PLAYLIST,
            raw_url=parsed.raw_url,
            playlist_id=uploads_id,
            channel_id=channel_id,
            handle=parsed.handle,
            custom_name=parsed.custom_name,
            user_name=parsed.user_name,
        )

    def list_videos(self, parsed: ParsedYoutubeInput, *, limit: int) -> list[YoutubeVideo]:
        resolved = parsed if parsed.playlist_id else self.resolve(parsed.raw_url)
        playlist_id = resolved.playlist_id
        if not playlist_id:
            raise YoutubeNotFound()

        videos: list[YoutubeVideo] = []
        page_token: str | None = None
        while len(videos) < limit:
            remaining = limit - len(videos)
            page = self._playlist_page(playlist_id, page_token, min(50, remaining))
            items = page.get("items") or []
            if not items and not videos:
                break
            for item in items:
                snippet = item.get("snippet") or {}
                resource = snippet.get("resourceId") or {}
                video_id = resource.get("videoId")
                title = snippet.get("title") or ""
                if not video_id:
                    continue
                videos.append(YoutubeVideo(video_id=video_id, title=title))
                if len(videos) >= limit:
                    break
            page_token = page.get("nextPageToken")
            if not page_token:
                break
        return videos

    def _lookup_channel_id(self, parsed: ParsedYoutubeInput) -> str:
        query = parsed.handle or parsed.custom_name or parsed.user_name
        if not query:
            raise YoutubeNotFound()
        payload = self._execute(self._client.search().list(part="snippet", q=query, type="channel", maxResults=1))
        items = payload.get("items") or []
        if not items:
            raise YoutubeNotFound()
        channel_id = (items[0].get("id") or {}).get("channelId")
        if not channel_id:
            raise YoutubeNotFound()
        return channel_id

    def _uploads_playlist(self, channel_id: str) -> str:
        payload = self._execute(self._client.channels().list(part="contentDetails", id=channel_id))
        items = payload.get("items") or []
        if not items:
            raise YoutubeNotFound()
        related = (items[0].get("contentDetails") or {}).get("relatedPlaylists") or {}
        uploads = related.get("uploads")
        if not uploads:
            raise YoutubeNotFound()
        return uploads

    def _playlist_page(self, playlist_id: str, page_token: str | None, max_results: int) -> dict[str, Any]:
        request = self._client.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=max_results,
            pageToken=page_token,
        )
        try:
            return self._execute(request)
        except YoutubeNotFound as exc:
            raise YoutubePaginationFailed(request_id=exc.request_id) from exc

    def _execute(self, request: Any) -> dict[str, Any]:
        self._consume_budget()
        started = time.perf_counter()

        def _call() -> dict[str, Any]:
            try:
                return request.execute()
            except HttpError as exc:
                request_id = ""
                if getattr(exc, "resp", None) is not None:
                    request_id = exc.resp.get("x-request-id") or exc.resp.get("X-Request-Id") or ""
                status = getattr(exc, "status_code", None) or getattr(exc.resp, "status", None)
                if status in {403, 429} and "quota" in str(exc).lower():
                    raise YoutubeQuotaExceeded(request_id=request_id) from exc
                if status == 404:
                    raise YoutubeNotFound(request_id=request_id) from exc
                if status in {500, 502, 503, 504}:
                    raise YoutubePaginationFailed(request_id=request_id) from exc
                raise YoutubePaginationFailed(request_id=request_id) from exc

        payload = retry_with_jitter(_call, attempts=3)
        duration_ms = (time.perf_counter() - started) * 1000
        job_log(
            logger,
            "youtube.request",
            job_id=self._job_id,
            provider="youtube",
            stage="fetch",
            duration_ms=round(duration_ms, 1),
            correlation_id=self._correlation_id,
        )
        return payload

    def _consume_budget(self) -> None:
        if self._requests_used >= self._request_budget:
            raise BudgetExceeded(code="BUDGET_EXCEEDED")
        self._requests_used += 1
