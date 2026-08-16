import pytest

from apps.playlist_sync.jobs import classify_job
from apps.playlist_sync.models import SyncJob
from apps.playlist_sync.tasks import classify_playlist_task


@pytest.mark.django_db
def test_eager_classify_task(job):
    classify_playlist_task.delay(job.id)
    job.refresh_from_db()
    assert job.status == SyncJob.Status.AWAITING_REVIEW
    assert job.track_mappings.count() == 5


@pytest.mark.django_db
def test_classify_persists_prompt_version(job, youtube, spotify, classifier):
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    job.refresh_from_db()
    assert job.classifier_prompt_version
    assert job.tokens_used > 0
