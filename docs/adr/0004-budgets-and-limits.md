# ADR 0004: Budgets and limits

## Status

Accepted

## Context

Unbounded playlists, retries, and AI calls can exhaust YouTube quota, Spotify rate limits, and OpenAI spend. The showcase must demonstrate explicit budgets.

## Decision

Per sync job:

| Limit | Value |
| --- | --- |
| Maximum videos processed | 200 |
| Job wall-clock timeout | 10 minutes |
| YouTube API request budget | 80 list/search calls |
| Spotify API request budget | 120 calls |
| Approximate AI cost budget | USD 0.50 |
| Classifier timeout | 20 seconds per video |
| Spotify search timeout | 10 seconds |
| YouTube connect/read timeout | 10 seconds |

When a budget is exceeded the job stops, persists progress, and fails with `BUDGET_EXCEEDED`. Partial mappings already stored remain available for review if classification finished some items.

These values are environment-configurable (`SYNC_MAX_PLAYLIST_SIZE`, `SYNC_JOB_TIMEOUT_SECONDS`, and related settings) so the demo can use smaller fixtures.

## Consequences

- Provider adapters count requests and raise mapped errors instead of looping forever.
- Pagination stops at the video cap rather than fetching an entire huge channel.
- Cost is estimated from token usage × a configured USD-per-token rate, not billed invoices.
