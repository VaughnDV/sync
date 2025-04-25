from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SyncJob, TrackMapping
from .forms import SyncJobForm, TrackMappingForm
from .services import YouTubeService, SpotifyService, OpenAIService
from spotipy.exceptions import SpotifyException
from django.urls import reverse

@login_required
def sync_playlist(request):
    if request.method == 'POST':
        if not request.user.spotify_access_token:
            messages.error(request, "Please connect your Spotify account first.")
            return redirect('social:begin', 'spotify')

        form = SyncJobForm(request.POST)
        if form.is_valid():
            sync_job = form.save(commit=False)
            sync_job.user = request.user
            
            # Check if an existing playlist was selected
            existing_playlist_id = request.POST.get('existing_playlist')
            if existing_playlist_id:
                sync_job.spotify_playlist_id = existing_playlist_id
                # Get the playlist name from Spotify
                spotify_service = SpotifyService(request.user)
                try:
                    playlist = spotify_service.sp.playlist(existing_playlist_id)
                    sync_job.spotify_playlist_name = playlist['name']
                except Exception as e:
                    messages.warning(request, f"Could not fetch playlist name: {str(e)}")
            
            sync_job.save()

            # Start the sync process
            youtube_service = YouTubeService()
            spotify_service = SpotifyService(request.user)
            openai_service = OpenAIService()

            try:
                # Get YouTube videos (from playlist or channel)
                videos = youtube_service.get_videos_from_url(sync_job.youtube_playlist_url)
                total_items = len(videos)
                
                if total_items == 0:
                    raise Exception("No videos found.")
                
                if total_items > 100:
                    messages.warning(request, f"Large collection detected ({total_items} videos). This may take a while.")
                
                # Process each video
                processed_count = 0
                for video in videos:
                    processed_count += 1
                    if processed_count % 10 == 0:
                        messages.info(request, f"Processing video {processed_count} of {total_items}...")
                    
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
                
                messages.success(request, f"Successfully processed {total_items} videos!")
                return redirect('playlist_sync:review', sync_job.id)
            except SpotifyException as e:
                sync_job.status = 'failed'
                sync_job.save()
                if e.http_status == 401:
                    error_msg = "Your Spotify session has expired. Please reconnect your account."
                else:
                    error_msg = f"Spotify API error: {str(e)}"
                return render(request, 'playlist_sync/sync_playlist.html', {
                    'form': form,
                    'error': error_msg
                })
            except Exception as e:
                sync_job.status = 'failed'
                sync_job.save()
                return render(request, 'playlist_sync/sync_playlist.html', {
                    'form': form,
                    'error': f'Error during sync: {str(e)}'
                })
    else:
        form = SyncJobForm()
        spotify_playlists = []
        
        if request.user.spotify_access_token:
            try:
                spotify_service = SpotifyService(request.user)
                playlists = spotify_service.sp.current_user_playlists()
                spotify_playlists = [{'id': p['id'], 'name': p['name']} for p in playlists['items']]
            except Exception as e:
                messages.warning(request, f"Could not fetch Spotify playlists: {str(e)}")

    return render(request, 'playlist_sync/sync_playlist.html', {
        'form': form,
        'spotify_playlists': spotify_playlists
    })

@login_required
def review_sync(request, job_id):
    sync_job = SyncJob.objects.get(id=job_id, user=request.user)
    track_mappings = sync_job.track_mappings.all()
    
    if request.method == 'POST':
        try:
            # Create or update Spotify playlist
            spotify_service = SpotifyService(request.user)
            track_ids = [mapping.spotify_track_id for mapping in track_mappings]
            
            if sync_job.reverse_order:
                track_ids.reverse()
            
            # Handle Spotify's limit of 100 tracks per request
            playlist_id = None
            for i in range(0, len(track_ids), 100):
                chunk = track_ids[i:i + 100]
                if not playlist_id:
                    playlist_id = spotify_service.create_or_update_playlist(
                        sync_job.spotify_playlist_name,
                        chunk
                    )
                else:
                    spotify_service.sp.playlist_add_items(playlist_id, chunk)
            
            sync_job.spotify_playlist_id = playlist_id
            sync_job.save()
            
            messages.success(request, 'Playlist synced successfully!')
            return redirect('dashboard:dashboard')
        except SpotifyException as e:
            if e.http_status == 401:
                messages.error(request, "Your Spotify session has expired. Please reconnect your account.")
                return redirect('social:begin', 'spotify')
            else:
                messages.error(request, f"Spotify API error: {str(e)}")
    
    return render(request, 'playlist_sync/review.html', {
        'sync_job': sync_job,
        'track_mappings': track_mappings
    }) 