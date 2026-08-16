import logging
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.exceptions import SyncError, YoutubeInvalidUrl
from providers.factory import get_spotify_client

from .forms import SyncJobForm
from .jobs import get_or_create_job, request_cancel
from .models import SyncJob, TrackMapping
from .tasks import apply_playlist_task, classify_playlist_task

logger = logging.getLogger(__name__)


def _owned_job(request, job_id: int) -> SyncJob:
    return get_object_or_404(SyncJob, id=job_id, user=request.user)


@login_required
def sync_playlist(request):
    spotify_playlists = []
    if request.method == "POST":
        if not request.user.spotify_connected:
            messages.error(request, "Please connect your Spotify account first.")
            return redirect("social:begin", "spotify")
        form = SyncJobForm(request.POST)
        if form.is_valid():
            try:
                idempotency_key = form.cleaned_data.get("idempotency_key") or uuid.uuid4().hex
                job, created = get_or_create_job(
                    user=request.user,
                    url=form.cleaned_data["youtube_playlist_url"],
                    name=form.cleaned_data["spotify_playlist_name"],
                    playlist_id=form.cleaned_data.get("spotify_playlist_id") or "",
                    reverse=form.cleaned_data.get("reverse_order") or False,
                    idempotency_key=idempotency_key,
                )
                if created:
                    task = classify_playlist_task.delay(job.id)
                    job.task_id = task.id
                    job.save(update_fields=["task_id"])
                messages.info(request, "Playlist classification started. Review the proposed tracks when it finishes.")
                return redirect("playlist_sync:review", job.id)
            except YoutubeInvalidUrl:
                messages.error(request, "That YouTube URL is not a supported playlist or channel link.")
            except SyncError as exc:
                messages.error(request, exc.user_message)
        return render(
            request,
            "playlist_sync/sync_playlist.html",
            {"form": form, "spotify_playlists": spotify_playlists},
        )

    form = SyncJobForm(initial={"idempotency_key": uuid.uuid4().hex})
    if request.user.spotify_connected:
        try:
            client = get_spotify_client(request.user)
            spotify_playlists = [{"id": item.playlist_id, "name": item.name} for item in client.list_playlists()]
        except SyncError as exc:
            messages.warning(request, exc.user_message)
    return render(
        request,
        "playlist_sync/sync_playlist.html",
        {"form": form, "spotify_playlists": spotify_playlists},
    )


@login_required
def review_sync(request, job_id: int):
    sync_job = _owned_job(request, job_id)
    track_mappings = sync_job.track_mappings.all().order_by("pk")
    if request.method == "POST":
        selected = [int(value) for value in request.POST.getlist("include") if value.isdigit()]
        apply_playlist_task.delay(sync_job.id, mapping_ids=selected)
        messages.info(request, "Creating the Spotify playlist from the confirmed tracks.")
        return redirect("playlist_sync:review", sync_job.id)
    return render(
        request,
        "playlist_sync/review.html",
        {
            "sync_job": sync_job,
            "track_mappings": track_mappings,
            "proposed": track_mappings.filter(decision=TrackMapping.Decision.PROPOSED),
            "needs_review": track_mappings.filter(decision=TrackMapping.Decision.NEEDS_REVIEW),
            "skipped": track_mappings.filter(
                decision__in=[TrackMapping.Decision.SKIPPED, TrackMapping.Decision.UNMATCHED]
            ),
        },
    )


@login_required
@require_POST
def cancel_sync(request, job_id: int):
    job = _owned_job(request, job_id)
    request_cancel(job)
    messages.info(request, "Cancellation requested.")
    return redirect("playlist_sync:review", job.id)


@login_required
def get_playlists(request):
    if not request.user.spotify_connected:
        return JsonResponse({"error": "Spotify not connected"}, status=401)
    try:
        client = get_spotify_client(request.user)
        return JsonResponse(
            {"playlists": [{"id": item.playlist_id, "name": item.name} for item in client.list_playlists()]}
        )
    except SyncError as exc:
        status = 401 if exc.code == "SPOTIFY_REVOKED" else 500
        return JsonResponse({"error": exc.user_message, "code": exc.code}, status=status)


@login_required
def get_sync_status(request, job_id: int):
    sync_job = _owned_job(request, job_id)
    return JsonResponse(
        {
            "status": sync_job.status,
            "error_code": sync_job.error_code,
            "error": sync_job.error_message,
            "current": sync_job.progress_current,
            "total": sync_job.progress_total,
            "stage": sync_job.progress_stage,
            "correlation_id": sync_job.correlation_id,
        }
    )
