from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from googleapiclient.errors import HttpError
from httplib2 import Response

from core.exceptions import BudgetExceeded, YoutubeNotFound, YoutubePaginationFailed, YoutubeQuotaExceeded
from providers import youtube as youtube_module
from providers.interfaces import ParsedYoutubeInput, YoutubeInputKind
from providers.youtube import LiveYouTubeClient


@pytest.fixture
def live_client(monkeypatch):
    client = object.__new__(LiveYouTubeClient)
    client._api_key = "key"
    client._timeout = 5
    client._request_budget = 20
    client._requests_used = 0
    client._job_id = 1
    client._correlation_id = "corr"
    client._client = MagicMock()
    monkeypatch.setattr(youtube_module, "retry_with_jitter", lambda operation, attempts: operation())
    return client


def _http_error(status: int, message: str, request_id: str = "request-1") -> HttpError:
    response = Response({"status": str(status), "x-request-id": request_id})
    return HttpError(response, message.encode(), uri="https://youtube.test")


def test_constructor_builds_google_client(monkeypatch):
    http = MagicMock()
    monkeypatch.setattr(youtube_module.httplib2, "Http", MagicMock(return_value=http))
    build = MagicMock(return_value="youtube-client")
    monkeypatch.setattr(youtube_module, "build", build)

    client = LiveYouTubeClient(api_key="key", timeout=3, request_budget=4)

    assert client._client == "youtube-client"
    build.assert_called_once_with("youtube", "v3", developerKey="key", http=http, cache_discovery=False)


def test_resolve_returns_playlist_without_api_call(live_client):
    parsed = live_client.resolve("https://www.youtube.com/playlist?list=PLdemodemo01")
    assert parsed.kind is YoutubeInputKind.PLAYLIST
    assert parsed.playlist_id == "PLdemodemo01"


def test_resolve_channel_uses_lookup_and_uploads(monkeypatch, live_client):
    monkeypatch.setattr(live_client, "_lookup_channel_id", MagicMock(return_value="UC123"))
    monkeypatch.setattr(live_client, "_uploads_playlist", MagicMock(return_value="UU123"))
    parsed = live_client.resolve("https://www.youtube.com/@example")
    assert parsed.playlist_id == "UU123"
    assert parsed.channel_id == "UC123"
    assert parsed.handle == "example"


def test_list_videos_paginates_and_honours_limit(monkeypatch, live_client):
    parsed = ParsedYoutubeInput(YoutubeInputKind.PLAYLIST, "raw", playlist_id="PL1")
    pages = [
        {
            "items": [
                {"snippet": {"title": "One", "resourceId": {"videoId": "v1"}}},
                {"snippet": {"title": "Missing id", "resourceId": {}}},
            ],
            "nextPageToken": "next",
        },
        {"items": [{"snippet": {"title": "Two", "resourceId": {"videoId": "v2"}}}]},
    ]
    monkeypatch.setattr(live_client, "_playlist_page", MagicMock(side_effect=pages))
    videos = live_client.list_videos(parsed, limit=2)
    assert [(video.video_id, video.title) for video in videos] == [("v1", "One"), ("v2", "Two")]


def test_list_videos_resolves_missing_playlist_and_handles_empty(monkeypatch, live_client):
    unresolved = ParsedYoutubeInput(YoutubeInputKind.CHANNEL, "raw", channel_id="UC1")
    resolved = ParsedYoutubeInput(YoutubeInputKind.PLAYLIST, "raw", playlist_id="PL1")
    monkeypatch.setattr(live_client, "resolve", MagicMock(return_value=resolved))
    monkeypatch.setattr(live_client, "_playlist_page", MagicMock(return_value={"items": []}))
    assert live_client.list_videos(unresolved, limit=5) == []

    monkeypatch.setattr(live_client, "resolve", MagicMock(return_value=unresolved))
    with pytest.raises(YoutubeNotFound):
        live_client.list_videos(unresolved, limit=5)


def test_lookup_channel_id_success_and_failures(monkeypatch, live_client):
    parsed = ParsedYoutubeInput(YoutubeInputKind.CHANNEL, "raw", handle="artist")
    monkeypatch.setattr(live_client, "_execute", MagicMock(return_value={"items": [{"id": {"channelId": "UC1"}}]}))
    assert live_client._lookup_channel_id(parsed) == "UC1"

    missing_query = ParsedYoutubeInput(YoutubeInputKind.CHANNEL, "raw")
    with pytest.raises(YoutubeNotFound):
        live_client._lookup_channel_id(missing_query)

    for payload in ({"items": []}, {"items": [{"id": {}}]}):
        monkeypatch.setattr(live_client, "_execute", MagicMock(return_value=payload))
        with pytest.raises(YoutubeNotFound):
            live_client._lookup_channel_id(parsed)


def test_uploads_playlist_success_and_failures(monkeypatch, live_client):
    monkeypatch.setattr(
        live_client,
        "_execute",
        MagicMock(return_value={"items": [{"contentDetails": {"relatedPlaylists": {"uploads": "UU1"}}}]}),
    )
    assert live_client._uploads_playlist("UC1") == "UU1"

    for payload in ({"items": []}, {"items": [{"contentDetails": {}}]}):
        monkeypatch.setattr(live_client, "_execute", MagicMock(return_value=payload))
        with pytest.raises(YoutubeNotFound):
            live_client._uploads_playlist("UC1")


def test_playlist_page_maps_not_found(monkeypatch, live_client):
    monkeypatch.setattr(live_client, "_execute", MagicMock(side_effect=YoutubeNotFound(request_id="req")))
    with pytest.raises(YoutubePaginationFailed) as caught:
        live_client._playlist_page("PL1", None, 10)
    assert caught.value.request_id == "req"


def test_execute_success(live_client):
    request = MagicMock()
    request.execute.return_value = {"items": [1]}
    assert live_client._execute(request) == {"items": [1]}
    assert live_client._requests_used == 1


@pytest.mark.parametrize(
    ("status", "message", "expected"),
    [
        (403, "quota exceeded", YoutubeQuotaExceeded),
        (429, "quota exceeded", YoutubeQuotaExceeded),
        (404, "missing", YoutubeNotFound),
        (500, "server", YoutubePaginationFailed),
        (400, "bad request", YoutubePaginationFailed),
    ],
)
def test_execute_maps_http_errors(status, message, expected, live_client):
    request = MagicMock()
    request.execute.side_effect = _http_error(status, message)
    with pytest.raises(expected) as caught:
        live_client._execute(request)
    assert caught.value.request_id == "request-1"


def test_request_budget_is_enforced(live_client):
    live_client._requests_used = live_client._request_budget
    with pytest.raises(BudgetExceeded) as caught:
        live_client._consume_budget()
    assert caught.value.code == "BUDGET_EXCEEDED"
