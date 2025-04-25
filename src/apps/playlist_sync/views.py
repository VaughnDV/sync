from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import SyncJob, TrackMapping
from .forms import SyncJobForm, TrackMappingForm
from .services import YouTubeService, SpotifyService, OpenAIService
from spotipy.exceptions import SpotifyException
from django.urls import reverse

@login_required
def sync_playlist(request):
    spotify_playlists = []  # Initialize at the beginning of the function
    
    if request.method == 'POST':
        if not request.user.spotify_access_token:
            messages.error(request, "Please connect your Spotify account first.")
            return redirect('social:begin', 'spotify')

        form = SyncJobForm(request.POST)
        if form.is_valid():
            sync_job = form.save(commit=False)
            sync_job.user = request.user
            sync_job.status = 'pending'
            
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
                    return render(request, 'playlist_sync/sync_playlist.html', {
                        'form': form,
                        'error': f"Could not fetch playlist name: {str(e)}",
                        'spotify_playlists': spotify_playlists
                    })
            else:
                # If no existing playlist selected, use the name from the form
                sync_job.spotify_playlist_name = form.cleaned_data['spotify_playlist_name']
            
            sync_job.save()

            # Start the sync process asynchronously
            from .tasks import sync_playlist_task
            task = sync_playlist_task.delay(sync_job.id)
            sync_job.task_id = task.id
            sync_job.save()

            messages.info(request, "Playlist sync started. This may take a while. You'll be notified when it's complete.")
            return redirect('playlist_sync:review', sync_job.id)
    else:
        form = SyncJobForm()
        
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

@login_required
def get_playlists(request):
    """AJAX endpoint to fetch user's Spotify playlists."""
    if not request.user.spotify_access_token:
        return JsonResponse({'error': 'Spotify not connected'}, status=401)
    
    try:
        spotify_service = SpotifyService(request.user)
        playlists = spotify_service.sp.current_user_playlists()
        return JsonResponse({
            'playlists': [{'id': p['id'], 'name': p['name']} for p in playlists['items']]
        })
    except SpotifyException as e:
        if e.http_status == 401:
            return JsonResponse({'error': 'Spotify token expired'}, status=401)
        return JsonResponse({'error': str(e)}, status=500)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_sync_status(request, job_id):
    """API endpoint to check sync job status"""
    try:
        sync_job = SyncJob.objects.get(id=job_id, user=request.user)
        if sync_job.task_id:
            from celery.result import AsyncResult
            task_result = AsyncResult(sync_job.task_id)
            
            response_data = {
                'status': sync_job.status,
                'task_status': task_result.status,
            }
            
            if task_result.status == 'PROGRESS':
                response_data.update(task_result.info)
            elif task_result.status == 'SUCCESS':
                response_data['result'] = task_result.get()
            elif task_result.status == 'FAILURE':
                response_data['error'] = str(task_result.result)
                
            return JsonResponse(response_data)
        else:
            return JsonResponse({'status': sync_job.status})
    except SyncJob.DoesNotExist:
        return JsonResponse({'error': 'Job not found'}, status=404) 