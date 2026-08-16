import pytest

from apps.playlist_sync.jobs import apply_job, classify_job
from apps.playlist_sync.models import SyncJob, TrackMapping
from providers.fakes import FakeSongClassifier, FakeSpotifyClient, FakeYouTubeClient


@pytest.mark.django_db
def test_worker_restart_after_partial_progress(job):
    youtube = FakeYouTubeClient()
    spotify = FakeSpotifyClient()
    seen: list[str] = []

    def boom(video):
        seen.append(video.video_id)
        if video.video_id == "vidPython1":
            raise RuntimeError("worker crash")

    classifier = FakeSongClassifier(on_classify=boom)
    with pytest.raises(RuntimeError):
        classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    created = job.track_mappings.count()
    assert created >= 1
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=FakeSongClassifier())
    job.refresh_from_db()
    assert job.status == SyncJob.Status.AWAITING_REVIEW
    assert job.track_mappings.count() == 5


@pytest.mark.django_db
def test_apply_resume_skips_completed_batches(job):
    youtube = FakeYouTubeClient()
    spotify = FakeSpotifyClient()
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=FakeSongClassifier())
    proposed = list(job.track_mappings.filter(decision=TrackMapping.Decision.PROPOSED))
    job.spotify_write_checkpoint = 1
    job.status = SyncJob.Status.AWAITING_REVIEW
    job.save()
    apply_job(job.id, spotify=spotify, mapping_ids=[item.pk for item in proposed])
    job.refresh_from_db()
    assert job.status == SyncJob.Status.COMPLETED
    assert spotify.added_batches == []
