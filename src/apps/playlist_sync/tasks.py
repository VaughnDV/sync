from celery import shared_task
from .models import SyncJob, TrackMapping
from .services import YouTubeService, SpotifyService, OpenAIService
from spotipy.exceptions import SpotifyException
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def sync_playlist_task(self, job_id):
    try:
        logger.info(f"Starting sync task for job {job_id}")
        
        with transaction.atomic():
            sync_job = SyncJob.objects.select_for_update().get(id=job_id)
            sync_job.status = 'processing'
            sync_job.save()

        youtube_service = YouTubeService()
        spotify_service = SpotifyService(sync_job.user)
        openai_service = OpenAIService()

        # Get YouTube videos
        videos = youtube_service.get_videos_from_url(sync_job.youtube_playlist_url)
        total_items = len(videos)
        
        if total_items == 0:
            raise Exception("No videos found in the YouTube playlist.")
        
        logger.info(f"Found {total_items} videos to process")
        
        # Process each video
        processed_count = 0
        for video in videos:
            processed_count += 1
            logger.info(f"Processing video {processed_count}/{total_items}: {video['title']}")
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': processed_count,
                    'total': total_items,
                    'status': f'Processing video {processed_count} of {total_items}...'
                }
            )
            
            try:
                # Use OpenAI to identify if it's a cover and get original artist/song
                original_info = openai_service.identify_original_song(video['title'])
                
                if original_info:
                    logger.info(f"Found original song info: {original_info}")
                    
                    # Search Spotify for the original song
                    spotify_track = spotify_service.search_track(
                        original_info['artist'],
                        original_info['song']
                    )
                    
                    if spotify_track:
                        logger.info(f"Found matching Spotify track: {spotify_track['name']}")
                        
                        # Create track mapping
                        with transaction.atomic():
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
                    else:
                        logger.warning(f"No matching Spotify track found for: {original_info}")
                else:
                    logger.warning(f"Could not identify original song for: {video['title']}")
                    
            except Exception as e:
                logger.error(f"Error processing video {video['title']}: {str(e)}")
                continue

        # Update job status to completed
        with transaction.atomic():
            sync_job.status = 'completed'
            sync_job.save()
            
        return {
            'status': 'completed',
            'total_videos': total_items,
            'processed_videos': processed_count
        }
            
    except Exception as e:
        logger.error(f"Error in sync_playlist_task: {str(e)}")
        with transaction.atomic():
            sync_job.status = 'failed'
            sync_job.save()
        raise self.retry(exc=e, countdown=60) 