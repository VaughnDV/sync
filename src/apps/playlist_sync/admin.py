from django.contrib import admin

from .models import ClassificationCache, SyncJob, TrackMapping


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "error_code",
        "spotify_playlist_name",
        "progress_current",
        "progress_total",
        "created_at",
    )
    list_filter = ("status", "error_code", "created_at")
    search_fields = ("user__email", "correlation_id", "idempotency_key")
    ordering = ("-created_at",)
    raw_id_fields = ("user",)
    readonly_fields = ("correlation_id", "idempotency_key", "error_code", "error_message")


@admin.register(TrackMapping)
class TrackMappingAdmin(admin.ModelAdmin):
    list_display = (
        "sync_job",
        "youtube_video_id",
        "decision",
        "classification",
        "confidence_score",
        "spotify_track_id",
    )
    list_filter = ("decision", "classification")
    search_fields = ("youtube_video_id", "original_artist", "original_song")
    raw_id_fields = ("sync_job",)


@admin.register(ClassificationCache)
class ClassificationCacheAdmin(admin.ModelAdmin):
    list_display = ("youtube_video_id", "classifier_version", "expires_at")
    search_fields = ("youtube_video_id",)
