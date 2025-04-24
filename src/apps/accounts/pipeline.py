from datetime import datetime, timedelta

def save_spotify_tokens(backend, user, response, *args, **kwargs):
    if backend.name == 'spotify':
        if response.get('access_token'):
            user.spotify_access_token = response.get('access_token')
            user.spotify_refresh_token = response.get('refresh_token')
            # Set token expiration time (Spotify tokens expire in 1 hour)
            expires_in = response.get('expires_in', 3600)
            user.spotify_token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            user.save() 