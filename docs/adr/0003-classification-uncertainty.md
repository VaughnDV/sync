# ADR 0003: Non-music and uncertain classifications

## Status

Accepted

## Context

Not every YouTube video is a song. The classifier can also be wrong or under-confident. Auto-adding those items pollutes Spotify playlists.

## Decision

Each video is classified into exactly one of:

- `music` — treat as a song (original, cover, or lesson) and attempt Spotify matching.
- `not_music` — skip. Persist as `skipped` with a user-facing reason.
- `uncertain` — do not auto-include. Persist as `needs_review`.

A result is also treated as `needs_review` when:

- `classification == music` but `confidence < 0.70`
- artist or song is missing after validation
- Spotify search returns no acceptable match

The review UI shows three buckets: **proposed**, **needs review**, and **skipped**. The user can include or exclude items before the apply step. Only items in the confirmed set are written to Spotify.

Prompt and schema version `song-classification/v1` is stored on every classification result.

## Consequences

- Structured output must include classification, artist, song, and confidence.
- Low-confidence music is visible rather than silently dropped.
- Fixtures cover malformed, missing, and contradictory model output.
