from __future__ import annotations

from prometheus_client import Counter, Histogram

jobs_started = Counter("sync_jobs_started_total", "Sync jobs started", ["stage"])
jobs_outcomes = Counter("sync_jobs_outcomes_total", "Terminal job outcomes", ["status", "error_code"])
job_retries = Counter("sync_job_retries_total", "Celery retries", ["stage"])
provider_errors = Counter("sync_provider_errors_total", "Mapped provider errors", ["provider", "code"])
unmatched_tracks = Counter("sync_unmatched_tracks_total", "Videos with no Spotify match")
classifier_confidence = Counter(
    "sync_classifier_confidence_bucket_total",
    "Classifier confidence buckets",
    ["bucket"],
)
provider_latency = Histogram(
    "sync_provider_latency_seconds",
    "Provider call latency",
    ["provider", "stage"],
)


def confidence_bucket(score: float | None) -> str:
    if score is None:
        return "none"
    if score < 0.5:
        return "low"
    if score < 0.7:
        return "medium"
    return "high"
