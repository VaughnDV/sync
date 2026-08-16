from __future__ import annotations

from providers.interfaces import SpotifyTrack


def rank_spotify_tracks(tracks: list[SpotifyTrack], artist: str, song: str) -> SpotifyTrack | None:
    if not tracks:
        return None

    def score(track: SpotifyTrack) -> int:
        value = 0
        if track.name.lower() == song.lower():
            value += 4
        elif song.lower() in track.name.lower():
            value += 2
        names = {item.name.lower() for item in track.artists}
        if artist.lower() in names:
            value += 4
        elif any(artist.lower() in name for name in names):
            value += 2
        if track.popularity:
            value += 1
        return value

    ranked = sorted(tracks, key=score, reverse=True)
    best = ranked[0]
    return best if score(best) >= 1 else None
