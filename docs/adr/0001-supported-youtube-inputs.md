# ADR 0001: Supported YouTube inputs

## Status

Accepted

## Context

The existing application accepted playlist URLs and several channel URL forms, but parsing was string-splitting and error messages mixed invalid input with provider failures. The showcase needs a documented, testable contract.

## Decision

Sync accepts:

1. **YouTube playlist URLs** as the primary input. Supported forms include `youtube.com/playlist?list=`, `youtube.com/watch?v=...&list=`, `youtu.be/...?...&list=`, and `music.youtube.com` playlist URLs.
2. **YouTube channel URLs**, which are resolved to the channel's uploads playlist. Supported forms: `/channel/{id}`, `/c/{custom}`, `/@{handle}`, and `/user/{name}`.

Single-video URLs without a `list=` parameter, shortened non-YouTube hosts, and malformed URLs are rejected with error code `YOUTUBE_INVALID_URL` before any provider call.

Channel resolution may require a YouTube Data API lookup. That lookup counts against the per-job provider request budget.

## Consequences

- URL parsing is a pure function with no SDK dependency and is unit-tested for every supported form.
- Playlist enumeration is always the downstream operation, even for channel URLs.
- The UI copy describes playlists as the intended product; channel support is a convenience that maps to uploads.
