from __future__ import annotations

TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"classifying", "cancelled", "failed"}),
    "classifying": frozenset({"awaiting_review", "cancelled", "failed"}),
    "awaiting_review": frozenset({"applying", "cancelled", "failed"}),
    "applying": frozenset({"completed", "cancelled", "failed"}),
    "completed": frozenset(),
    "failed": frozenset(),
    "cancelled": frozenset(),
}


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())


def is_terminal(status: str) -> bool:
    return status in TERMINAL_STATUSES
