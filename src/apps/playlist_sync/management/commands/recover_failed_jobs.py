from django.core.management.base import BaseCommand

from apps.playlist_sync.models import SyncJob
from apps.playlist_sync.tasks import apply_playlist_task, classify_playlist_task


class Command(BaseCommand):
    help = "Re-queue failed or stuck jobs for manual recovery (dead-letter handling)."

    def add_arguments(self, parser):
        parser.add_argument("--job-id", type=int, help="Recover a single job")
        parser.add_argument("--apply", action="store_true", help="Re-queue apply instead of classify")

    def handle(self, *args, **options):
        queryset = SyncJob.objects.filter(
            status__in=[SyncJob.Status.FAILED, SyncJob.Status.CLASSIFYING, SyncJob.Status.APPLYING]
        )
        if options.get("job_id"):
            queryset = queryset.filter(pk=options["job_id"])
        count = 0
        for job in queryset:
            if options.get("apply") or job.status == SyncJob.Status.APPLYING:
                job.status = SyncJob.Status.AWAITING_REVIEW
                job.error_code = ""
                job.error_message = ""
                job.save(update_fields=["status", "error_code", "error_message"])
                apply_playlist_task.delay(job.id)
            else:
                job.status = SyncJob.Status.PENDING
                job.error_code = ""
                job.error_message = ""
                job.save(update_fields=["status", "error_code", "error_message"])
                classify_playlist_task.delay(job.id)
            count += 1
            self.stdout.write(f"requeued job {job.pk}")
        self.stdout.write(self.style.SUCCESS(f"requeued {count} job(s)"))
