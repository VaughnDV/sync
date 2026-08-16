import pytest

from apps.playlist_sync.jobs import apply_job, classify_job
from apps.playlist_sync.models import SyncJob, TrackMapping
from core.exceptions import SpotifyPartialBatch, SpotifyRateLimited, SpotifyRevoked
from providers.fakes import FakeSpotifyClient


@pytest.mark.django_db
def test_spotify_revoked_during_search(job, youtube, classifier):
    spotify = FakeSpotifyClient(revoked=True)
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    job.refresh_from_db()
    assert job.status == SyncJob.Status.FAILED
    assert job.error_code == "SPOTIFY_REVOKED"


@pytest.mark.django_db
def test_spotify_rate_limit_is_retryable(job, youtube, classifier):
    spotify = FakeSpotifyClient(rate_limited=True)
    with pytest.raises(SpotifyRateLimited):
        classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)


@pytest.mark.django_db
def test_partial_batch_failure_keeps_checkpoint(job, youtube, classifier):
    spotify = FakeSpotifyClient(fail_batch_at=0)
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    job.refresh_from_db()
    proposed = list(job.track_mappings.filter(decision=TrackMapping.Decision.PROPOSED))
    apply_job(job.id, spotify=spotify, mapping_ids=[item.pk for item in proposed])
    job.refresh_from_db()
    assert job.status == SyncJob.Status.FAILED
    assert job.error_code == "SPOTIFY_PARTIAL_BATCH"
    assert job.spotify_write_checkpoint == 0


def test_spotify_fake_error_types():
    with pytest.raises(SpotifyRevoked):
        FakeSpotifyClient(revoked=True).list_playlists()
    with pytest.raises(SpotifyRateLimited):
        FakeSpotifyClient(rate_limited=True).list_playlists()
    client = FakeSpotifyClient(fail_batch_at=0)
    client.create_playlist("x")
    with pytest.raises(SpotifyPartialBatch):
        client.add_tracks("pl000001", ["a"])
