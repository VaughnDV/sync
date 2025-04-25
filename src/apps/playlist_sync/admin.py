from django.contrib import admin
from .models import SyncJob, TrackMapping

@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'youtube_playlist_url', 'spotify_playlist_id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('user__email', 'user__username', 'youtube_playlist_url', 'spotify_playlist_id')
    ordering = ('-created_at',)
    raw_id_fields = ('user',)

@admin.register(TrackMapping)
class TrackMappingAdmin(admin.ModelAdmin):
    list_display = ('sync_job', 'youtube_video_id', 'original_artist', 'original_title', 'spotify_track_id', 'confidence_score')
    list_filter = ('confidence_score', 'created_at')
    search_fields = ('youtube_video_id', 'original_artist', 'original_title', 'spotify_track_id')
    ordering = ('-created_at',)
    raw_id_fields = ('sync_job',) 