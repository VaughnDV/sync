from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.playlist_sync.models import ClassificationCache, SyncJob


class Command(BaseCommand):
    help = "Delete expired classification cache, old jobs, and disconnected Spotify tokens."

    def add_arguments(self, parser):
        parser.add_argument("--job-days", type=int, default=90)
        parser.add_argument("--token-days", type=int, default=30)

    def handle(self, *args, **options):
        now = timezone.now()
        cache_deleted, _ = ClassificationCache.objects.filter(expires_at__lt=now).delete()
        job_cutoff = now - timedelta(days=options["job_days"])
        jobs_deleted, _ = SyncJob.objects.filter(created_at__lt=job_cutoff).delete()
        token_cutoff = now - timedelta(days=options["token_days"])
        disconnected = User.objects.filter(spotify_connected=False, spotify_token_expires_at__lt=token_cutoff)
        token_count = disconnected.count()
        disconnected.update(spotify_access_token="", spotify_refresh_token="", spotify_token_expires_at=None)
        self.stdout.write(
            self.style.SUCCESS(
                f"purged cache={cache_deleted} jobs={jobs_deleted} disconnected_tokens={token_count}"
            )
        )
