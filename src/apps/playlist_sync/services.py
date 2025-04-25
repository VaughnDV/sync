import os
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from openai import OpenAI
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self):
        logger.info("Initializing YouTubeService")
        self.youtube = build('youtube', 'v3', developerKey=settings.YOUTUBE_API_KEY)

    def get_videos_from_url(self, url):
        logger.info(f"Processing YouTube URL: {url}")
        try:
            # Check if it's a playlist URL
            if 'list=' in url:
                logger.debug("URL identified as playlist")
                return self.get_playlist_items(url)
            # Check if it's a channel URL
            elif 'youtube.com/channel/' in url or 'youtube.com/c/' in url or 'youtube.com/@' in url:
                logger.debug("URL identified as channel")
                return self.get_channel_videos(url)
            else:
                logger.warning(f"Invalid YouTube URL format: {url}")
                raise Exception('Invalid YouTube URL. Please provide a playlist or channel URL.')
        except Exception as e:
            logger.error(f"Error processing YouTube URL: {str(e)}")
            raise Exception(f'Error processing YouTube URL: {str(e)}')

    def get_playlist_items(self, playlist_url):
        logger.info(f"Fetching playlist items from URL: {playlist_url}")
        try:
            # Extract playlist ID from URL
            playlist_id = self._extract_playlist_id(playlist_url)
            logger.debug(f"Extracted playlist ID: {playlist_id}")
            
            items = []
            next_page_token = None
            
            while True:
                logger.debug(f"Fetching playlist items page (token: {next_page_token})")
                # Get playlist items
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token
                )
                response = request.execute()
                
                # Add items from current page
                for item in response['items']:
                    items.append({
                        'id': item['snippet']['resourceId']['videoId'],
                        'title': item['snippet']['title']
                    })
                
                # Check if there are more pages
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            logger.info(f"Successfully fetched {len(items)} items from playlist")
            return items
        except HttpError as e:
            logger.error(f"YouTube API error: {str(e)}")
            raise Exception(f'YouTube API error: {str(e)}')

    def get_channel_videos(self, channel_url):
        logger.info(f"Fetching channel videos from URL: {channel_url}")
        try:
            # Extract channel ID from URL
            channel_id = self._extract_channel_id(channel_url)
            logger.debug(f"Extracted channel ID: {channel_id}")
            
            # First, get the uploads playlist ID
            request = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            response = request.execute()
            
            if not response['items']:
                logger.warning(f"Channel not found: {channel_id}")
                raise Exception('Channel not found')
            
            uploads_playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            logger.debug(f"Found uploads playlist ID: {uploads_playlist_id}")
            
            # Now get the videos from the uploads playlist
            return self.get_playlist_items(f'https://www.youtube.com/playlist?list={uploads_playlist_id}')
        except HttpError as e:
            logger.error(f"YouTube API error: {str(e)}")
            raise Exception(f'YouTube API error: {str(e)}')

    def _extract_playlist_id(self, url):
        logger.debug(f"Extracting playlist ID from URL: {url}")
        # Extract playlist ID from various YouTube URL formats
        if 'list=' in url:
            playlist_id = url.split('list=')[1].split('&')[0]
            logger.debug(f"Extracted playlist ID: {playlist_id}")
            return playlist_id
        logger.warning(f"Invalid playlist URL format: {url}")
        raise Exception('Invalid YouTube playlist URL')

    def _extract_channel_id(self, url):
        logger.debug(f"Extracting channel ID from URL: {url}")
        # Extract channel ID from various YouTube URL formats
        if 'youtube.com/channel/' in url:
            channel_id = url.split('youtube.com/channel/')[1].split('/')[0]
            logger.debug(f"Extracted channel ID: {channel_id}")
            return channel_id
        elif 'youtube.com/c/' in url:
            # For custom URLs, we need to get the channel ID
            custom_url = url.split('youtube.com/c/')[1].split('/')[0]
            logger.debug(f"Looking up channel ID for custom URL: {custom_url}")
            request = self.youtube.search().list(
                part='snippet',
                q=custom_url,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            if response['items']:
                channel_id = response['items'][0]['id']['channelId']
                logger.debug(f"Found channel ID for custom URL: {channel_id}")
                return channel_id
            logger.warning(f"Channel not found for custom URL: {custom_url}")
            raise Exception('Channel not found')
        elif 'youtube.com/@' in url:
            # For @username URLs
            username = url.split('youtube.com/@')[1].split('/')[0]
            logger.debug(f"Looking up channel ID for username: {username}")
            request = self.youtube.search().list(
                part='snippet',
                q=username,
                type='channel',
                maxResults=1
            )
            response = request.execute()
            if response['items']:
                channel_id = response['items'][0]['id']['channelId']
                logger.debug(f"Found channel ID for username: {channel_id}")
                return channel_id
            logger.warning(f"Channel not found for username: {username}")
            raise Exception('Channel not found')
        logger.warning(f"Invalid channel URL format: {url}")
        raise Exception('Invalid YouTube channel URL')

class SpotifyService:
    def __init__(self, user):
        logger.info(f"Initializing SpotifyService for user: {user.username}")
        self.sp = spotipy.Spotify(auth=user.spotify_access_token)

    def search_track(self, artist, song):
        logger.info(f"Searching Spotify for track: {song} by {artist}")
        try:
            query = f'artist:{artist} track:{song}'
            logger.debug(f"Search query: {query}")
            results = self.sp.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                logger.debug(f"Found track: {track['name']} by {track['artists'][0]['name']}")
                return {
                    'id': track['id'],
                    'name': track['name'],
                    'artists': [{'name': artist['name']} for artist in track['artists']]
                }
            logger.warning(f"No track found for query: {query}")
            return None
        except Exception as e:
            logger.error(f"Spotify API error: {str(e)}")
            raise Exception(f'Spotify API error: {str(e)}')

    def create_or_update_playlist(self, name, track_ids):
        logger.info(f"Creating/updating playlist: {name} with {len(track_ids)} tracks")
        try:
            # Get user's playlists
            playlists = self.sp.current_user_playlists()
            playlist_id = None
            
            # Check if playlist exists
            for playlist in playlists['items']:
                if playlist['name'] == name:
                    playlist_id = playlist['id']
                    logger.debug(f"Found existing playlist: {name} (ID: {playlist_id})")
                    break
            
            if playlist_id:
                # Clear existing tracks
                logger.debug(f"Clearing existing tracks from playlist: {playlist_id}")
                self.sp.playlist_replace_items(playlist_id, [])
            else:
                # Create new playlist
                user_id = self.sp.current_user()['id']
                logger.debug(f"Creating new playlist for user: {user_id}")
                playlist = self.sp.user_playlist_create(user_id, name)
                playlist_id = playlist['id']
                logger.info(f"Created new playlist: {name} (ID: {playlist_id})")
            
            # Add tracks to playlist
            logger.debug(f"Adding {len(track_ids)} tracks to playlist: {playlist_id}")
            self.sp.playlist_add_items(playlist_id, track_ids)
            
            return playlist_id
        except Exception as e:
            logger.error(f"Spotify API error: {str(e)}")
            raise Exception(f'Spotify API error: {str(e)}')

class OpenAIService:
    def __init__(self):
        logger.info("Initializing OpenAIService")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def identify_original_song(self, video_title):
        logger.info(f"Identifying original song for video title: {video_title}")
        try:
            prompt = f"""
            Analyze this YouTube video title and determine if it's a cover song or an original song or lesson for a song.
            If it is a cover song or an original song or lesson for a song, identify the original artist and song name.
            Title: "{video_title}"
            
            Respond in this exact format:
            is_cover: true/false
            artist: [original artist name]
            song: [original song name]
            confidence: [0-1]
            """
            
            logger.debug("Sending request to OpenAI API")
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a music expert who can identify cover songs and their original versions. Always respond in the exact format specified."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = response.choices[0].message.content
            logger.debug(f"OpenAI response: {result}")
            
            # Parse the response
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            if len(lines) < 4:
                logger.warning("Invalid response format from OpenAI")
                return None
                
            is_cover = 'is_cover: true' in lines[0].lower()
            if not is_cover:
                logger.info("No cover song identified")
                return None
                
            try:
                artist = lines[1].split(': ')[1].strip()
                song = lines[2].split(': ')[1].strip()
                confidence_str = lines[3].split(': ')[1].strip()
                confidence = float(confidence_str)
                
                logger.info(f"Identified cover song: {song} by {artist} (confidence: {confidence})")
                return {
                    'artist': artist,
                    'song': song,
                    'confidence': confidence
                }
            except (IndexError, ValueError) as e:
                logger.error(f"Error parsing OpenAI response: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f'OpenAI API error: {str(e)}') 