import pytest

from apps.playlist_sync.jobs import classify_job
from apps.playlist_sync.models import TrackMapping
from core.exceptions import AIRateLimited
from providers.fakes import FakeSongClassifier
from providers.interfaces import YoutubeVideo


@pytest.mark.django_db
def test_ai_timeout_records_review_row(job, youtube, spotify):
    classifier = FakeSongClassifier(timeout_ids=["vidHello01"])
    with pytest.raises(Exception):
        classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    mapping = TrackMapping.objects.get(sync_job=job, youtube_video_id="vidHello01")
    assert mapping.decision == TrackMapping.Decision.NEEDS_REVIEW
    assert mapping.skip_reason == "AI_TIMEOUT"


@pytest.mark.django_db
def test_ai_invalid_schema_and_refusal(job, youtube, spotify):
    classifier = FakeSongClassifier(malformed_ids=["vidWonder1"], refusal_ids=["vidPython1"])
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    job.refresh_from_db()
    wonder = job.track_mappings.get(youtube_video_id="vidWonder1")
    tutorial = job.track_mappings.get(youtube_video_id="vidPython1")
    assert wonder.decision == TrackMapping.Decision.NEEDS_REVIEW
    assert tutorial.decision == TrackMapping.Decision.SKIPPED


@pytest.mark.django_db
def test_ai_rate_limit_retries(job, youtube, spotify):
    classifier = FakeSongClassifier(rate_limit=True)
    with pytest.raises(AIRateLimited):
        classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)


def test_classifier_timeout_unit():
    with pytest.raises(Exception):
        FakeSongClassifier(timeout_ids=["x"]).classify(YoutubeVideo("x", "t"))
