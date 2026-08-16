from django.conf import settings
from django.db import models

from core.ids import new_correlation_id


class SyncJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CLASSIFYING = "classifying", "Classifying"
        AWAITING_REVIEW = "awaiting_review", "Awaiting review"
        APPLYING = "applying", "Applying"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sync_jobs")
    youtube_playlist_url = models.URLField()
    source_kind = models.CharField(max_length=20, default="playlist")
    spotify_playlist_name = models.CharField(max_length=255)
    spotify_playlist_id = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.CharField(max_length=64)
    task_id = models.CharField(max_length=255, blank=True, default="")
    reverse_order = models.BooleanField(default=False)
    cancel_requested = models.BooleanField(default=False)
    error_code = models.CharField(max_length=64, blank=True, default="")
    error_message = models.CharField(max_length=255, blank=True, default="")
    progress_current = models.PositiveIntegerField(default=0)
    progress_total = models.PositiveIntegerField(default=0)
    progress_stage = models.CharField(max_length=32, blank=True, default="")
    spotify_write_checkpoint = models.PositiveIntegerField(default=0)
    correlation_id = models.CharField(max_length=36, default=new_correlation_id)
    classifier_prompt_version = models.CharField(max_length=64, blank=True, default="")
    tokens_used = models.PositiveIntegerField(default=0)
    estimated_cost_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    provider_requests = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "idempotency_key"], name="unique_user_idempotency"),
        ]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"job-{self.pk}:{self.status}"


class TrackMapping(models.Model):
    class Decision(models.TextChoices):
        PROPOSED = "proposed", "Proposed"
        NEEDS_REVIEW = "needs_review", "Needs review"
        SKIPPED = "skipped", "Skipped"
        UNMATCHED = "unmatched", "Unmatched"
        CONFIRMED = "confirmed", "Confirmed"
        EXCLUDED = "excluded", "Excluded"
        WRITTEN = "written", "Written"

    sync_job = models.ForeignKey(SyncJob, on_delete=models.CASCADE, related_name="track_mappings")
    youtube_video_id = models.CharField(max_length=32)
    youtube_video_title = models.CharField(max_length=255)
    original_artist = models.CharField(max_length=255, blank=True, default="")
    original_song = models.CharField(max_length=255, blank=True, default="")
    spotify_track_id = models.CharField(max_length=255, blank=True, default="")
    spotify_track_name = models.CharField(max_length=255, blank=True, default="")
    spotify_artist_name = models.CharField(max_length=255, blank=True, default="")
    confidence_score = models.FloatField(null=True, blank=True)
    classification = models.CharField(max_length=20, blank=True, default="")
    classifier_version = models.CharField(max_length=64, blank=True, default="")
    decision = models.CharField(max_length=20, choices=Decision.choices, default=Decision.PROPOSED)
    skip_reason = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["sync_job", "youtube_video_id"], name="unique_job_video"),
        ]

    def __str__(self) -> str:
        return f"{self.youtube_video_id}->{self.spotify_track_id or self.decision}"


class ClassificationCache(models.Model):
    cache_key = models.CharField(max_length=64, unique=True)
    youtube_video_id = models.CharField(max_length=32)
    normalised_title = models.CharField(max_length=255)
    payload = models.JSONField()
    classifier_version = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=["expires_at"])]

    def __str__(self) -> str:
        return self.cache_key
