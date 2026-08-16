import pytest
from django.test import Client
from django.urls import reverse

from apps.playlist_sync.jobs import apply_job, classify_job
from apps.playlist_sync.models import SyncJob, TrackMapping
from providers.fakes import (
    DEMO_PLAYLIST_URL,
    FakeSongClassifier,
    FakeSpotifyClient,
    FakeYouTubeClient,
)


@pytest.mark.django_db
def test_offline_submit_classify_review_apply(user):
    youtube = FakeYouTubeClient()
    spotify = FakeSpotifyClient()
    classifier = FakeSongClassifier()
    job = SyncJob.objects.create(
        user=user,
        youtube_playlist_url=DEMO_PLAYLIST_URL,
        spotify_playlist_name="Offline demo",
        idempotency_key="offline-1",
    )
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    job.refresh_from_db()
    assert job.status == SyncJob.Status.AWAITING_REVIEW
    proposed = list(job.track_mappings.filter(decision=TrackMapping.Decision.PROPOSED))
    skipped = list(job.track_mappings.filter(decision=TrackMapping.Decision.SKIPPED))
    review = list(job.track_mappings.filter(decision=TrackMapping.Decision.NEEDS_REVIEW))
    assert proposed
    assert skipped
    assert review
    apply_job(job.id, spotify=spotify, mapping_ids=[item.pk for item in proposed])
    job.refresh_from_db()
    assert job.status == SyncJob.Status.COMPLETED
    assert job.spotify_playlist_id
    assert spotify.created_playlists
    assert spotify.added_batches


@pytest.mark.django_db
def test_http_offline_flow(user):
    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("playlist_sync:sync_playlist"),
        {
            "youtube_playlist_url": DEMO_PLAYLIST_URL,
            "spotify_playlist_name": "HTTP demo",
            "idempotency_key": "http-1",
        },
    )
    assert response.status_code == 302
    job = SyncJob.objects.get(user=user, idempotency_key="http-1")
    assert job.status in {SyncJob.Status.AWAITING_REVIEW, SyncJob.Status.CLASSIFYING, SyncJob.Status.COMPLETED}
    review = client.get(reverse("playlist_sync:review", args=[job.pk]))
    assert review.status_code == 200
