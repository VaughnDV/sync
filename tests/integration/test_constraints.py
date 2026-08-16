import pytest
from django.db import IntegrityError

from apps.playlist_sync.models import SyncJob, TrackMapping


@pytest.mark.django_db
def test_mapping_uniqueness(job):
    TrackMapping.objects.create(
        sync_job=job,
        youtube_video_id="vidHello01",
        youtube_video_title="Hello",
    )
    with pytest.raises(IntegrityError):
        TrackMapping.objects.create(
            sync_job=job,
            youtube_video_id="vidHello01",
            youtube_video_title="Hello again",
        )


@pytest.mark.django_db
def test_idempotency_key_uniqueness(user, job):
    with pytest.raises(IntegrityError):
        SyncJob.objects.create(
            user=user,
            youtube_playlist_url=job.youtube_playlist_url,
            spotify_playlist_name="other",
            idempotency_key=job.idempotency_key,
        )
