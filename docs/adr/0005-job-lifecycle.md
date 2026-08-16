# ADR 0005: Job cancellation, retry, and resume

## Status

Accepted

## Context

Celery retries currently re-run classification and can duplicate `TrackMapping` rows. There is no cancel path and no distinction between "classified, waiting for review" and "writing to Spotify".

## Decision

Job states:

```
pending → classifying → awaiting_review → applying → completed
              ↓                ↓              ↓
          cancelled        cancelled      cancelled
              ↓                ↓              ↓
            failed           failed         failed
```

Rules:

- **Idempotency key**: unique per user. A duplicate submit with the same key returns the existing job instead of starting another.
- **Uniqueness**: `(sync_job, youtube_video_id)` is unique. Retries upsert mappings rather than inserting duplicates.
- **Resume**: classification skips video IDs that already have a mapping. Apply skips batches already recorded in `spotify_write_checkpoint`.
- **Cancel**: allowed from `pending`, `classifying`, and `applying`. Workers check a `cancel_requested` flag between items. Terminal cancel is `cancelled`.
- **Timeout**: a job past the wall-clock budget is marked `failed` with `JOB_TIMEOUT`.
- **Duplicate task delivery**: the worker takes a `select_for_update` lock and refuses to run if status is already `completed`, `cancelled`, or `applying` for an apply task that has finished.
- **Retries**: at most three attempts with exponential backoff and jitter. Retries resume; they do not restart from scratch.

Classification never writes to Spotify. Apply never re-classifies.

## Consequences

- Two Celery tasks: `classify_playlist_task` and `apply_playlist_task`.
- Progress and `error_code` are stored on the job, not only in the Celery result backend.
- Failure tests cover worker restart and duplicate delivery.
