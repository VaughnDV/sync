# Sanitised API examples

All examples assume a logged-in session cookie. Tokens never appear in responses.

## Submit a playlist

`POST /playlist/`

```
youtube_playlist_url=https://www.youtube.com/playlist?list=PLdemodemo01
spotify_playlist_name=Demo
idempotency_key=offline-demo-1
```

Redirects to `/playlist/review/<job_id>/`.

## Job status

`GET /playlist/status/1/`

```json
{
  "status": "awaiting_review",
  "error_code": "",
  "error": "",
  "current": 5,
  "total": 5,
  "stage": "review",
  "correlation_id": "11111111-2222-3333-4444-555555555555"
}
```

## Health

`GET /health/live/` → `{"status": "live"}`

`GET /health/ready/` → `{"status": "ready", "checks": {"database": true}}`
