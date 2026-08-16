from __future__ import annotations

import logging
import time
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.exceptions import JobCancelled, SyncError, TransientSyncError
from core.logging import job_log
from core.metrics import (
    classifier_confidence,
    confidence_bucket,
    jobs_outcomes,
    jobs_started,
    provider_errors,
    unmatched_tracks,
)
from providers.interfaces import SongClassifier, SpotifyClient, YouTubeClient, YoutubeVideo
from providers.schemas import PROMPT_VERSION
from providers.youtube_urls import parse_youtube_url

from .diffing import SPOTIFY_ADD_LIMIT, build_playlist_diff
from .models import SyncJob, TrackMapping
from .state import can_transition, is_terminal

logger = logging.getLogger(__name__)


def _fail(job: SyncJob, error: SyncError | Exception) -> None:
    if isinstance(error, SyncError):
        job.error_code = error.code
        job.error_message = error.user_message
    else:
        job.error_code = "INTERNAL_ERROR"
        job.error_message = "Something went wrong. The failure was recorded without exposing internals."
    job.status = SyncJob.Status.FAILED
    job.finished_at = timezone.now()
    job.save(update_fields=["error_code", "error_message", "status", "finished_at", "updated_at"])
    jobs_outcomes.labels(status=job.status, error_code=job.error_code or "none").inc()
    provider_errors.labels(provider="job", code=job.error_code or "INTERNAL_ERROR").inc()
    job_log(
        logger,
        "job.failed",
        job_id=job.pk,
        stage=job.progress_stage,
        correlation_id=job.correlation_id,
        error_code=job.error_code,
    )


def _cancel(job: SyncJob) -> None:
    job.status = SyncJob.Status.CANCELLED
    job.error_code = "JOB_CANCELLED"
    job.error_message = "This job was cancelled."
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "error_code", "error_message", "finished_at", "updated_at"])
    jobs_outcomes.labels(status=job.status, error_code=job.error_code).inc()


def _check_cancel(job: SyncJob) -> None:
    job.refresh_from_db(fields=["cancel_requested", "status"])
    if job.cancel_requested or job.status == SyncJob.Status.CANCELLED:
        raise JobCancelled()


def _check_timeout(job: SyncJob) -> None:
    started = job.started_at or job.created_at
    elapsed = (timezone.now() - started).total_seconds()
    if elapsed > settings.SYNC_JOB_TIMEOUT_SECONDS:
        from core.exceptions import JobTimeout

        raise JobTimeout()


def classify_job(
    job_id: int,
    *,
    youtube: YouTubeClient,
    spotify: SpotifyClient,
    classifier: SongClassifier,
) -> SyncJob:
    job = SyncJob.objects.select_related("user").get(pk=job_id)
    if is_terminal(job.status) and job.status != SyncJob.Status.PENDING:
        return job
    if job.status == SyncJob.Status.AWAITING_REVIEW:
        return job

    if can_transition(job.status, SyncJob.Status.CLASSIFYING) or job.status == SyncJob.Status.CLASSIFYING:
        job.status = SyncJob.Status.CLASSIFYING
        job.progress_stage = "classify"
        job.started_at = job.started_at or timezone.now()
        job.classifier_prompt_version = PROMPT_VERSION
        job.save(update_fields=["status", "progress_stage", "started_at", "classifier_prompt_version", "updated_at"])
        jobs_started.labels(stage="classify").inc()

    try:
        _check_cancel(job)
        _check_timeout(job)
        parsed = youtube.resolve(job.youtube_playlist_url)
        job.source_kind = parsed.kind.value
        videos = youtube.list_videos(parsed, limit=settings.SYNC_MAX_PLAYLIST_SIZE)
        if not videos:
            from core.exceptions import YoutubeNotFound

            raise YoutubeNotFound()
        job.progress_total = len(videos)
        job.save(update_fields=["source_kind", "progress_total", "updated_at"])

        existing = set(TrackMapping.objects.filter(sync_job=job).values_list("youtube_video_id", flat=True))
        for index, video in enumerate(videos, start=1):
            _check_cancel(job)
            _check_timeout(job)
            job.progress_current = index
            job.save(update_fields=["progress_current", "updated_at"])
            if video.video_id in existing:
                continue
            _classify_video(job, video, classifier, spotify)
            existing.add(video.video_id)

        job.status = SyncJob.Status.AWAITING_REVIEW
        job.progress_stage = "review"
        job.save(update_fields=["status", "progress_stage", "updated_at"])
        job_log(logger, "job.awaiting_review", job_id=job.pk, correlation_id=job.correlation_id, stage="review")
        return job
    except JobCancelled:
        _cancel(job)
        return job
    except TransientSyncError:
        raise
    except SyncError as exc:
        _fail(job, exc)
        return job
    except Exception:
        raise


def _classify_video(
    job: SyncJob,
    video: YoutubeVideo,
    classifier: SongClassifier,
    spotify: SpotifyClient,
) -> None:
    started = time.perf_counter()
    try:
        result = classifier.classify(video)
    except SyncError as exc:
        TrackMapping.objects.update_or_create(
            sync_job=job,
            youtube_video_id=video.video_id,
            defaults={
                "youtube_video_title": video.title,
                "decision": TrackMapping.Decision.NEEDS_REVIEW
                if exc.code != "AI_REFUSAL"
                else TrackMapping.Decision.SKIPPED,
                "skip_reason": exc.code,
                "classifier_version": PROMPT_VERSION,
            },
        )
        if exc.retryable:
            raise
        return

    job.tokens_used += result.tokens_used
    job.estimated_cost_usd = Decimal(job.estimated_cost_usd) + Decimal(str(result.estimated_cost_usd))
    job.save(update_fields=["tokens_used", "estimated_cost_usd", "updated_at"])

    decision = TrackMapping.Decision.PROPOSED
    skip_reason = ""
    spotify_track = None
    if result.classification == "not_music":
        decision = TrackMapping.Decision.SKIPPED
        skip_reason = "not_music"
    elif result.classification == "uncertain" or (
        result.classification == "music" and result.confidence < settings.SYNC_CONFIDENCE_THRESHOLD
    ):
        decision = TrackMapping.Decision.NEEDS_REVIEW
        skip_reason = "low_confidence"
    elif result.classification == "music":
        spotify_track = spotify.search_track(result.artist or "", result.song or "")
        if spotify_track is None:
            decision = TrackMapping.Decision.UNMATCHED
            skip_reason = "no_spotify_match"
    else:
        decision = TrackMapping.Decision.NEEDS_REVIEW
        skip_reason = "AI_INVALID_SCHEMA"

    TrackMapping.objects.update_or_create(
        sync_job=job,
        youtube_video_id=video.video_id,
        defaults={
            "youtube_video_title": video.title,
            "original_artist": result.artist or "",
            "original_song": result.song or "",
            "spotify_track_id": spotify_track.track_id if spotify_track else "",
            "spotify_track_name": spotify_track.name if spotify_track else "",
            "spotify_artist_name": spotify_track.primary_artist if spotify_track else "",
            "confidence_score": result.confidence,
            "classification": result.classification,
            "classifier_version": result.prompt_version,
            "decision": decision,
            "skip_reason": skip_reason,
        },
    )
    classifier_confidence.labels(bucket=confidence_bucket(result.confidence)).inc()
    if decision == TrackMapping.Decision.UNMATCHED:
        unmatched_tracks.inc()
    job_log(
        logger,
        "job.video_classified",
        job_id=job.pk,
        provider="classifier",
        stage="classify",
        duration_ms=round((time.perf_counter() - started) * 1000, 1),
        correlation_id=job.correlation_id,
        cached=result.cached,
        decision=decision,
    )


def apply_job(job_id: int, *, spotify: SpotifyClient, mapping_ids: list[int] | None = None) -> SyncJob:
    job = SyncJob.objects.select_related("user").get(pk=job_id)
    if job.status == SyncJob.Status.COMPLETED:
        return job
    if job.status not in {SyncJob.Status.AWAITING_REVIEW, SyncJob.Status.APPLYING}:
        if is_terminal(job.status):
            return job
        raise SyncError("Job is not ready to apply.", code="INTERNAL_ERROR")

    job.status = SyncJob.Status.APPLYING
    job.progress_stage = "apply"
    job.save(update_fields=["status", "progress_stage", "updated_at"])

    try:
        _check_cancel(job)
        _check_timeout(job)
        mappings = job.track_mappings.all()
        if mapping_ids is not None:
            mappings.filter(pk__in=mapping_ids).update(decision=TrackMapping.Decision.CONFIRMED)
            mappings.exclude(pk__in=mapping_ids).exclude(decision=TrackMapping.Decision.SKIPPED).update(
                decision=TrackMapping.Decision.EXCLUDED
            )
        else:
            mappings.filter(decision=TrackMapping.Decision.PROPOSED).update(decision=TrackMapping.Decision.CONFIRMED)

        confirmed = list(
            job.track_mappings.filter(decision__in=[TrackMapping.Decision.CONFIRMED, TrackMapping.Decision.WRITTEN])
            .exclude(spotify_track_id="")
            .order_by("pk")
        )
        existing_ids: list[str] = []
        playlist_id = job.spotify_playlist_id
        if playlist_id:
            existing_ids = spotify.list_playlist_track_ids(playlist_id)
        else:
            playlist_id = spotify.create_playlist(job.spotify_playlist_name)
            job.spotify_playlist_id = playlist_id
            job.save(update_fields=["spotify_playlist_id", "updated_at"])

        diff = build_playlist_diff(
            proposed_track_ids=[item.spotify_track_id for item in confirmed],
            existing_track_ids=existing_ids,
            reverse=job.reverse_order,
        )
        batches = diff.batches(SPOTIFY_ADD_LIMIT)
        for index, batch in enumerate(batches):
            _check_cancel(job)
            if index < job.spotify_write_checkpoint:
                continue
            spotify.add_tracks(playlist_id, batch)
            job.spotify_write_checkpoint = index + 1
            job.save(update_fields=["spotify_write_checkpoint", "updated_at"])

        job.track_mappings.filter(decision=TrackMapping.Decision.CONFIRMED).update(
            decision=TrackMapping.Decision.WRITTEN
        )
        job.status = SyncJob.Status.COMPLETED
        job.progress_stage = "done"
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "progress_stage", "finished_at", "updated_at"])
        jobs_outcomes.labels(status=job.status, error_code="none").inc()
        job_log(logger, "job.completed", job_id=job.pk, correlation_id=job.correlation_id, stage="apply")
        return job
    except JobCancelled:
        _cancel(job)
        return job
    except TransientSyncError:
        raise
    except SyncError as exc:
        _fail(job, exc)
        return job
    except Exception as exc:  # noqa: BLE001
        _fail(job, exc)
        raise


def request_cancel(job: SyncJob) -> SyncJob:
    if is_terminal(job.status):
        return job
    job.cancel_requested = True
    if job.status == SyncJob.Status.PENDING:
        _cancel(job)
        return job
    job.save(update_fields=["cancel_requested", "updated_at"])
    return job


def get_or_create_job(
    *,
    user,
    url: str,
    name: str,
    playlist_id: str,
    reverse: bool,
    idempotency_key: str,
) -> tuple[SyncJob, bool]:
    parse_youtube_url(url)
    with transaction.atomic():
        job, created = SyncJob.objects.get_or_create(
            user=user,
            idempotency_key=idempotency_key,
            defaults={
                "youtube_playlist_url": url,
                "spotify_playlist_name": name,
                "spotify_playlist_id": playlist_id or "",
                "reverse_order": reverse,
                "status": SyncJob.Status.PENDING,
            },
        )
    return job, created
