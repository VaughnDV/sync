import pytest

from core.exceptions import YoutubeInvalidUrl
from providers.youtube_urls import parse_youtube_url


@pytest.mark.parametrize(
    "url,playlist_id",
    [
        ("https://www.youtube.com/playlist?list=PLabcdefghij", "PLabcdefghij"),
        ("https://youtube.com/watch?v=abc123&list=PLabcdefghij", "PLabcdefghij"),
        ("https://m.youtube.com/playlist?list=PLabcdefghij&si=x", "PLabcdefghij"),
        ("https://music.youtube.com/playlist?list=PLabcdefghij", "PLabcdefghij"),
        ("https://www.youtube.com/watch?v=abc&list=UUabcdefghij", "UUabcdefghij"),
    ],
)
def test_playlist_urls(url, playlist_id):
    parsed = parse_youtube_url(url)
    assert parsed.kind.value == "playlist"
    assert parsed.playlist_id == playlist_id


@pytest.mark.parametrize(
    "url,field,value",
    [
        ("https://www.youtube.com/channel/UCabcdefghij", "channel_id", "UCabcdefghij"),
        ("https://www.youtube.com/c/CustomName", "custom_name", "CustomName"),
        ("https://www.youtube.com/@handle", "handle", "handle"),
        ("https://www.youtube.com/user/legacyname", "user_name", "legacyname"),
    ],
)
def test_channel_urls(url, field, value):
    parsed = parse_youtube_url(url)
    assert parsed.kind.value == "channel"
    assert getattr(parsed, field) == value


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://example.com/playlist?list=PLabcdefghij",
        "https://youtu.be/dQw4w9wgGcQ",
        "https://www.youtube.com/watch?v=dQw4w9wgGcQ",
        "https://www.youtube.com/playlist",
        "not a url",
    ],
)
def test_malformed_urls(url):
    with pytest.raises(YoutubeInvalidUrl):
        parse_youtube_url(url)
