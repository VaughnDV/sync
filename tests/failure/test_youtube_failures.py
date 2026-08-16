import pytest

from core.exceptions import YoutubePaginationFailed, YoutubeQuotaExceeded
from providers.fakes import FakeYouTubeClient
from providers.interfaces import ParsedYoutubeInput, YoutubeInputKind
from apps.playlist_sync.jobs import classify_job


@pytest.mark.django_db
def test_youtube_quota_exhaustion(job, spotify, classifier):
    youtube = FakeYouTubeClient(quota_exhausted=True)
    with pytest.raises(YoutubeQuotaExceeded):
        classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)


@pytest.mark.django_db
def test_youtube_pagination_failure(job, spotify, classifier):
    youtube = FakeYouTubeClient(fail_after_pages=0)
    with pytest.raises(YoutubePaginationFailed):
        classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)


def test_fake_youtube_raises_mapped_errors():
    parsed = ParsedYoutubeInput(kind=YoutubeInputKind.PLAYLIST, raw_url="x", playlist_id="PLdemodemo01")
    with pytest.raises(YoutubeQuotaExceeded):
        FakeYouTubeClient(quota_exhausted=True).list_videos(parsed, limit=10)
    with pytest.raises(YoutubePaginationFailed):
        FakeYouTubeClient(fail_after_pages=0).list_videos(parsed, limit=10)
