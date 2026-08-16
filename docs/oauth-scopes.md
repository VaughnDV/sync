# Spotify OAuth scopes

Sync requests the minimum Spotify scopes needed to list a user's playlists and append tracks to a **private** playlist:

- `playlist-read-private` — enumerate existing playlists so a job can append missing tracks instead of creating duplicates.
- `playlist-modify-private` — create a private playlist or add tracks to one the user owns.

The application does not request streaming, library, follow, or email scopes. Access and refresh tokens are encrypted at rest and are never rendered in Django admin, logs, exceptions, or model representations. Users can disconnect from `/accounts/spotify/disconnect/`, which clears local credentials and attempts provider revocation.
