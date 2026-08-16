from apps.playlist_sync.state import can_transition, is_terminal


def test_allowed_transitions():
    assert can_transition("pending", "classifying")
    assert can_transition("classifying", "awaiting_review")
    assert can_transition("awaiting_review", "applying")
    assert can_transition("applying", "completed")
    assert not can_transition("completed", "applying")
    assert not can_transition("failed", "pending")


def test_terminal_states():
    assert is_terminal("completed")
    assert is_terminal("failed")
    assert is_terminal("cancelled")
    assert not is_terminal("classifying")
