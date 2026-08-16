#!/usr/bin/env python
"""One-command offline demo: classify a fixture playlist and create a fake Spotify playlist."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
os.environ.setdefault("SYNC_TESTING", "1")
os.environ.setdefault("SYNC_PROVIDER_MODE", "fake")
os.environ.setdefault("DJANGO_SECRET_KEY", "demo-secret")
os.environ.setdefault("TOKEN_ENCRYPTION_KEY", "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=")
sys.path.insert(0, str(ROOT))

import django
from django.core.management import call_command

django.setup()
call_command("migrate", run_syncdb=True, verbosity=0)

from django.contrib.auth import get_user_model  # noqa: E402

from apps.playlist_sync.jobs import apply_job, classify_job  # noqa: E402
from apps.playlist_sync.models import SyncJob, TrackMapping  # noqa: E402
from providers.fakes import DEMO_PLAYLIST_URL, FakeSongClassifier, FakeSpotifyClient, FakeYouTubeClient  # noqa: E402


def main() -> int:
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        email="recruiter@example.com",
        defaults={"username": "recruiter"},
    )
    user.set_password("demo-password")
    user.spotify_connected = True
    user.spotify_access_token = "demo-access"
    user.save()

    job = SyncJob.objects.create(
        user=user,
        youtube_playlist_url=DEMO_PLAYLIST_URL,
        spotify_playlist_name="Sync offline demo",
        idempotency_key="demo-offline",
    )
    youtube = FakeYouTubeClient()
    spotify = FakeSpotifyClient()
    classifier = FakeSongClassifier()
    classify_job(job.id, youtube=youtube, spotify=spotify, classifier=classifier)
    job.refresh_from_db()
    proposed = list(job.track_mappings.filter(decision=TrackMapping.Decision.PROPOSED))
    apply_job(job.id, spotify=spotify, mapping_ids=[item.pk for item in proposed])
    job.refresh_from_db()

    print("Offline demo complete.")
    print(f"  job_id={job.pk} status={job.status} playlist={job.spotify_playlist_id}")
    print(f"  proposed={len(proposed)} written={job.track_mappings.filter(decision='written').count()}")
    print(f"  tokens={job.tokens_used} estimated_usd={job.estimated_cost_usd}")
    if job.status != SyncJob.Status.COMPLETED:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
