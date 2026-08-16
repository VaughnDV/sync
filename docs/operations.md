# Operations

## Health

- `GET /health/live/` — process is up.
- `GET /health/ready/` — database connection succeeds. Redis and RabbitMQ are required by Celery workers, not the web process.

Expected dependencies: PostgreSQL, Redis (Celery result backend), RabbitMQ (broker), and optionally YouTube/Spotify/OpenAI when `SYNC_PROVIDER_MODE=live`.

## Metrics and logs

- `GET /metrics/` — Prometheus counters for jobs, outcomes, retries, provider errors, unmatched tracks and classifier confidence buckets.
- Structured JSON logs include `job_id`, `provider`, `stage`, `attempt`, `duration_ms`, `correlation_id` and `error_code`. Tokens and raw user content are not logged at INFO.

## Dead-letter recovery

Failed or stuck jobs can be re-queued:

```bash
poetry run python src/manage.py recover_failed_jobs
poetry run python src/manage.py recover_failed_jobs --job-id 42 --apply
```

## Retention

| Data | Retention |
| --- | --- |
| Encrypted Spotify tokens | Cleared on disconnect; leftover disconnected tokens purged after 30 days |
| Sync jobs and track mappings | 90 days |
| Classification cache | Until `expires_at` (default 30 days) |

```bash
poetry run python src/manage.py purge_expired_data --job-days 90 --token-days 30
```
