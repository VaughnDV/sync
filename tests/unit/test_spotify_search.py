from apps.playlist_sync.matching import rank_spotify_tracks
from providers.interfaces import SpotifyArtist, SpotifyTrack


def _track(track_id, name, artist, popularity=0):
    return SpotifyTrack(track_id=track_id, name=name, artists=(SpotifyArtist(name=artist),), popularity=popularity)


def test_ranks_exact_artist_and_title():
    tracks = [
        _track("1", "Hello", "Someone", popularity=99),
        _track("2", "Hello", "Adele", popularity=10),
    ]
    best = rank_spotify_tracks(tracks, "Adele", "Hello")
    assert best is not None
    assert best.track_id == "2"


def test_no_match_returns_none():
    assert rank_spotify_tracks([], "Adele", "Hello") is None
    assert rank_spotify_tracks([_track("1", "Yellow", "Coldplay")], "Adele", "Hello") is None
