from celery import shared_task
from .models import SyncJob, TrackMapping
from .services import YouTubeService, SpotifyService, OpenAIService
from spotipy.exceptions import SpotifyException
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def sync_playlist_task(self, job_id):
    try:
        sync_job = SyncJob.objects.get(id=job_id)
        sync_job.status = 'processing'
        sync_job.save()

        youtube_service = YouTubeService()
        spotify_service = SpotifyService(sync_job.user)
        openai_service = OpenAIService()

        # Get YouTube videos
        videos = youtube_service.get_videos_from_url(sync_job.youtube_playlist_url)
        total_items = len(videos)
        
        if total_items == 0:
            raise Exception("No videos found.")
        
        # Process each video
        processed_count = 0
        for video in videos:
            processed_count += 1
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': processed_count,
                    'total': total_items,
                    'status': f'Processing video {processed_count} of {total_items}...'
                }
            )
            
            # Use OpenAI to identify if it's a cover and get original artist/song
            original_info = openai_service.identify_original_song(video['title'])
            
            if original_info:
                # Search Spotify for the original song
                spotify_track = spotify_service.search_track(
                    original_info['artist'],
                    original_info['song']
                )
                
                if spotify_track:
                    # Create track mapping
                    TrackMapping.objects.create(
                        sync_job=sync_job,
                        youtube_video_id=video['id'],
                        youtube_video_title=video['title'],
                        original_artist=original_info['artist'],
                        original_song=original_info['song'],
                        spotify_track_id=spotify_track['id'],
                        spotify_track_name=spotify_track['name'],
                        spotify_artist_name=spotify_track['artists'][0]['name'],
                        confidence_score=original_info['confidence']
                    )

        sync_job.status = 'completed'
        sync_job.save()
        
        return {
            'current': total_items,
            'total': total_items,
            'status': 'Task completed!',
            'result': 'Success'
        }
    except SpotifyException as e:
        sync_job.status = 'failed'
        sync_job.save()
        if e.http_status == 401:
            raise Exception("Spotify session expired. Please reconnect your account.")
        else:
            raise Exception(f"Spotify API error: {str(e)}")
    except Exception as e:
        sync_job.status = 'failed'
        sync_job.save()
        raise Exception(f'Error during sync: {str(e)}') 