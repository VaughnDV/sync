import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import openai
from django.conf import settings

class YouTubeService:
    def __init__(self):
        self.youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)

    def get_playlist_items(self, playlist_url):
        try:
            # Extract playlist ID from URL
            playlist_id = self._extract_playlist_id(playlist_url)
            
            # Get playlist items
            request = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50
            )
            response = request.execute()
            
            items = []
            for item in response['items']:
                items.append({
                    'id': item['snippet']['resourceId']['videoId'],
                    'title': item['snippet']['title']
                })
            
            return items
        except HttpError as e:
            raise Exception(f'YouTube API error: {str(e)}')

    def _extract_playlist_id(self, url):
        # Extract playlist ID from various YouTube URL formats
        if 'list=' in url:
            return url.split('list=')[1].split('&')[0]
        raise Exception('Invalid YouTube playlist URL')

class SpotifyService:
    def __init__(self, user):
        self.sp = spotipy.Spotify(auth=user.spotify_access_token)

    def search_track(self, artist, song):
        try:
            query = f'artist:{artist} track:{song}'
            results = self.sp.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return {
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [{'name': artist['name']} for artist in track['artists']]
                }
            return None
        except Exception as e:
            raise Exception(f'Spotify API error: {str(e)}')

    def create_or_update_playlist(self, name, track_ids):
        try:
            # Get user's playlists
            playlists = self.sp.current_user_playlists()
            playlist_id = None
            
            # Check if playlist exists
            for playlist in playlists['items']:
                if playlist['name'] == name:
                    playlist_id = playlist['id']
                    break
            
            if playlist_id:
                # Clear existing tracks
                self.sp.playlist_replace_items(playlist_id, [])
            else:
                # Create new playlist
                user_id = self.sp.current_user()['id']
                playlist = self.sp.user_playlist_create(user_id, name)
                playlist_id = playlist['id']
            
            # Add tracks to playlist
            self.sp.playlist_add_items(playlist_id, track_ids)
            
            return playlist_id
        except Exception as e:
            raise Exception(f'Spotify API error: {str(e)}')

class OpenAIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    def identify_original_song(self, video_title):
        try:
            prompt = f"""
            Analyze this YouTube video title and determine if it's a cover song or an original song or lesson for a song.
            If it is a cover song or an original song or lesson for a song, identify the original artist and song name.
            Title: "{video_title}"
            
            Respond in this format:
            is_cover: true/false
            artist: [original artist name]
            song: [original song name]
            confidence: [0-1]
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a music expert who can identify cover songs and their original versions."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = response.choices[0].message.content
            lines = result.split('\n')
            
            if 'is_cover: true' in lines[0].lower():
                return {
                    'artist': lines[1].split(': ')[1].strip(),
                    'song': lines[2].split(': ')[1].strip(),
                    'confidence': float(lines[3].split(': ')[1].strip())
                }
            return None
        except Exception as e:
            raise Exception(f'OpenAI API error: {str(e)}') 