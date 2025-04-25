from django.db import models
from django.conf import settings

class SyncJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    youtube_playlist_url = models.URLField()
    spotify_playlist_name = models.CharField(max_length=255)
    spotify_playlist_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    task_id = models.CharField(max_length=255, null=True, blank=True)
    reverse_order = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.youtube_playlist_url} -> {self.spotify_playlist_name}"

class TrackMapping(models.Model):
    sync_job = models.ForeignKey(SyncJob, on_delete=models.CASCADE, related_name='track_mappings')
    youtube_video_id = models.CharField(max_length=255)
    youtube_video_title = models.CharField(max_length=255)
    original_artist = models.CharField(max_length=255)
    original_song = models.CharField(max_length=255)
    spotify_track_id = models.CharField(max_length=255)
    spotify_track_name = models.CharField(max_length=255)
    spotify_artist_name = models.CharField(max_length=255)
    confidence_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.youtube_video_title} -> {self.spotify_track_name}" 