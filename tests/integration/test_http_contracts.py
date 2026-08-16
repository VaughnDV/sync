import json
from pathlib import Path

from apps.playlist_sync.matching import rank_spotify_tracks
from providers.interfaces import SpotifyArtist, SpotifyTrack, YoutubeVideo

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def test_sanitised_youtube_playlist_contract():
    payload = json.loads((FIXTURE_DIR / "youtube_playlist_page.json").read_text())
    videos = [
        YoutubeVideo(
            video_id=item["snippet"]["resourceId"]["videoId"],
            title=item["snippet"]["title"],
        )
        for item in payload["items"]
    ]
    assert payload["requestId"].startswith("yt-req-")
    assert videos[0].video_id == "vidHello01"


def test_sanitised_spotify_search_contract():
    payload = json.loads((FIXTURE_DIR / "spotify_search.json").read_text())
    tracks = [
        SpotifyTrack(
            track_id=item["id"],
            name=item["name"],
            artists=tuple(SpotifyArtist(name=artist["name"]) for artist in item["artists"]),
            popularity=item["popularity"],
        )
        for item in payload["tracks"]["items"]
    ]
    best = rank_spotify_tracks(tracks, "Adele", "Hello")
    assert best is not None
    assert best.track_id == "spHello01"
