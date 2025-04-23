from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SyncJob, TrackMapping
from .forms import SyncJobForm, TrackMappingForm
from .services import YouTubeService, SpotifyService, OpenAIService

@login_required
def sync_playlist(request):
    if request.method == 'POST':
        form = SyncJobForm(request.POST)
        if form.is_valid():
            sync_job = form.save(commit=False)
            sync_job.user = request.user
            sync_job.save()

            # Start the sync process
            youtube_service = YouTubeService()
            spotify_service = SpotifyService(request.user)
            openai_service = OpenAIService()

            try:
                # Get YouTube playlist items
                playlist_items = youtube_service.get_playlist_items(sync_job.youtube_playlist_url)
                
                # Process each video
                for item in playlist_items:
                    # Use OpenAI to identify if it's a cover and get original artist/song
                    original_info = openai_service.identify_original_song(item['title'])
                    
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
                                youtube_video_id=item['id'],
                                youtube_video_title=item['title'],
                                original_artist=original_info['artist'],
                                original_song=original_info['song'],
                                spotify_track_id=spotify_track['id'],
                                spotify_track_name=spotify_track['name'],
                                spotify_artist_name=spotify_track['artists'][0]['name'],
                                confidence_score=original_info['confidence']
                            )

                sync_job.status = 'completed'
                sync_job.save()
                
                return redirect('playlist_sync:review', sync_job.id)
            except Exception as e:
                sync_job.status = 'failed'
                sync_job.save()
                messages.error(request, f'Error during sync: {str(e)}')
    else:
        form = SyncJobForm()

    return render(request, 'playlist_sync/sync.html', {'form': form})

@login_required
def review_sync(request, job_id):
    sync_job = SyncJob.objects.get(id=job_id, user=request.user)
    track_mappings = sync_job.track_mappings.all()
    
    if request.method == 'POST':
        # Create or update Spotify playlist
        spotify_service = SpotifyService(request.user)
        track_ids = [mapping.spotify_track_id for mapping in track_mappings]
        
        if sync_job.reverse_order:
            track_ids.reverse()
            
        playlist_id = spotify_service.create_or_update_playlist(
            sync_job.spotify_playlist_name,
            track_ids
        )
        
        sync_job.spotify_playlist_id = playlist_id
        sync_job.save()
        
        messages.success(request, 'Playlist synced successfully!')
        return redirect('dashboard')
    
    return render(request, 'playlist_sync/review.html', {
        'sync_job': sync_job,
        'track_mappings': track_mappings
    }) 