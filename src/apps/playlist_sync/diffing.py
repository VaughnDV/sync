from __future__ import annotations

from dataclasses import dataclass, field

SPOTIFY_ADD_LIMIT = 100


@dataclass
class PlaylistDiff:
    to_add: list[str] = field(default_factory=list)
    already_present: list[str] = field(default_factory=list)
    skipped_video_ids: list[str] = field(default_factory=list)
    needs_review_video_ids: list[str] = field(default_factory=list)
    unmatched_video_ids: list[str] = field(default_factory=list)

    def batches(self, size: int = SPOTIFY_ADD_LIMIT) -> list[list[str]]:
        return [self.to_add[index : index + size] for index in range(0, len(self.to_add), size)]


def build_playlist_diff(
    *,
    proposed_track_ids: list[str],
    existing_track_ids: list[str],
    skipped_video_ids: list[str] | None = None,
    needs_review_video_ids: list[str] | None = None,
    unmatched_video_ids: list[str] | None = None,
    reverse: bool = False,
) -> PlaylistDiff:
    existing = set(existing_track_ids)
    ordered: list[str] = []
    seen: set[str] = set()
    for track_id in proposed_track_ids:
        if not track_id or track_id in seen:
            continue
        seen.add(track_id)
        ordered.append(track_id)
    if reverse:
        ordered.reverse()
    to_add = [track_id for track_id in ordered if track_id not in existing]
    already = [track_id for track_id in ordered if track_id in existing]
    return PlaylistDiff(
        to_add=to_add,
        already_present=already,
        skipped_video_ids=list(skipped_video_ids or []),
        needs_review_video_ids=list(needs_review_video_ids or []),
        unmatched_video_ids=list(unmatched_video_ids or []),
    )
