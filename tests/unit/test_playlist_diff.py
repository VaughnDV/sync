from apps.playlist_sync.diffing import SPOTIFY_ADD_LIMIT, build_playlist_diff


def test_appends_missing_and_skips_existing():
    diff = build_playlist_diff(
        proposed_track_ids=["a", "b", "c"],
        existing_track_ids=["b"],
    )
    assert diff.to_add == ["a", "c"]
    assert diff.already_present == ["b"]


def test_duplicate_suppression_and_reverse():
    diff = build_playlist_diff(
        proposed_track_ids=["a", "a", "b", ""],
        existing_track_ids=[],
        reverse=True,
    )
    assert diff.to_add == ["b", "a"]


def test_batch_limits():
    ids = [str(i) for i in range(SPOTIFY_ADD_LIMIT + 5)]
    diff = build_playlist_diff(proposed_track_ids=ids, existing_track_ids=[])
    batches = diff.batches()
    assert len(batches[0]) == SPOTIFY_ADD_LIMIT
    assert len(batches[1]) == 5
