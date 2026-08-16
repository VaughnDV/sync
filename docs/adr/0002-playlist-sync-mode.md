# ADR 0002: Playlist sync mode

## Status

Accepted

## Context

The current Spotify writer either creates a playlist or **clears and replaces** an existing one. Replacement is destructive and surprises users. The handover requires a defined strategy: replace, append missing tracks, or versioned playlists.

## Decision

Sync is **review-first append**:

1. Classification and Spotify search produce a proposed playlist diff. No Spotify playlist is mutated in this stage.
2. The user reviews proposed, uncertain, skipped, and unmatched tracks, then confirms.
3. On confirm:
   - If a target playlist was selected, **append tracks that are not already on it**. Existing items are never removed.
   - If no target playlist exists, **create one private playlist** and add the confirmed tracks.
4. Track order of newly added items follows YouTube order, or reverse YouTube order when the job requested it.

Versioned playlists (a new playlist per run) are out of scope for the showcase. Destructive replace is not offered.

## Consequences

- Classification is a separate Celery task from Spotify mutation.
- Diffing requires enumerating the target playlist with pagination before writes.
- Writes use 100-track batches and persist a checkpoint so retries do not duplicate inserts.
