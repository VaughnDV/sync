import pytest

from apps.playlist_sync.jobs import classify_job
from apps.playlist_sync.models import SyncJob
from providers.fakes import FakeSongClassifier, FakeSpotifyClient, FakeYouTubeClient


@pytest.mark.django_db
def test_duplicate_classify_delivery_does_not_duplicate_rows(job):
    youtube = FakeYouTubeClient()
    spotify = FakeSpotifyClient()
    classifier = FakeSongClassifier()
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    first_count = job.track_mappings.count()
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    job.refresh_from_db()
    assert job.status == SyncJob.Status.AWAITING_REVIEW
    assert job.track_mappings.count() == first_count == 5
