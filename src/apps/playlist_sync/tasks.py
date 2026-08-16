from __future__ import annotations

import logging

from celery import shared_task

from core.exceptions import TransientSyncError
from core.logging import job_log
from core.metrics import job_retries
from core.tracing import span
from providers.factory import get_classifier, get_spotify_client, get_youtube_client

from .jobs import apply_job, classify_job
from .models import ClassificationCache, SyncJob

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, autoretry_for=(TransientSyncError,), retry_backoff=True, retry_jitter=True)
def classify_playlist_task(self, job_id: int) -> dict:
    job = SyncJob.objects.select_related("user").get(pk=job_id)
    job_log(
        logger,
        "task.classify.start",
        job_id=job_id,
        stage="classify",
        attempt=self.request.retries + 1,
        correlation_id=job.correlation_id,
    )
    if self.request.retries:
        job_retries.labels(stage="classify").inc()
    youtube = get_youtube_client(job_id=job_id, correlation_id=job.correlation_id)
    spotify = get_spotify_client(job.user, job_id=job_id, correlation_id=job.correlation_id)
    classifier = get_classifier(
        job_id=job_id,
        correlation_id=job.correlation_id,
        cache_model=ClassificationCache,
    )
    with span(logger, "classify", job_id=job_id, stage="classify", correlation_id=job.correlation_id):
        classify_job(job_id, youtube=youtube, spotify=spotify, classifier=classifier)
    job.refresh_from_db()
    return {"status": job.status, "error_code": job.error_code}


@shared_task(bind=True, max_retries=3, autoretry_for=(TransientSyncError,), retry_backoff=True, retry_jitter=True)
def apply_playlist_task(self, job_id: int, mapping_ids: list[int] | None = None) -> dict:
    job = SyncJob.objects.select_related("user").get(pk=job_id)
    job_log(
        logger,
        "task.apply.start",
        job_id=job_id,
        stage="apply",
        attempt=self.request.retries + 1,
        correlation_id=job.correlation_id,
    )
    if self.request.retries:
        job_retries.labels(stage="apply").inc()
    spotify = get_spotify_client(job.user, job_id=job_id, correlation_id=job.correlation_id)
    with span(logger, "apply", job_id=job_id, provider="spotify", stage="apply", correlation_id=job.correlation_id):
        apply_job(job_id, spotify=spotify, mapping_ids=mapping_ids)
    job.refresh_from_db()
    return {"status": job.status, "error_code": job.error_code}


# Backwards-compatible alias used by older call sites / docs.
sync_playlist_task = classify_playlist_task
