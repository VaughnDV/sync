from datetime import timedelta

from django.utils import timezone


def save_spotify_tokens(backend, user, response, *args, **kwargs):
    if backend.name != "spotify":
        return
    access = response.get("access_token")
    if not access:
        return
    user.spotify_access_token = access
    if response.get("refresh_token"):
        user.spotify_refresh_token = response.get("refresh_token")
    expires_in = int(response.get("expires_in") or 3600)
    user.spotify_token_expires_at = timezone.now() + timedelta(seconds=expires_in)
    user.spotify_connected = True
    user.save(
        update_fields=[
            "spotify_access_token",
            "spotify_refresh_token",
            "spotify_token_expires_at",
            "spotify_connected",
        ]
    )
