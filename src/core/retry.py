from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from core.exceptions import TransientSyncError

T = TypeVar("T")


def retry_with_jitter(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 0.4,
    max_delay: float = 8.0,
    sleeper: Callable[[float], None] = time.sleep,
) -> T:
    """Run *operation* with bounded retries and full-jitter backoff."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except TransientSyncError as exc:
            last_error = exc
            if attempt >= attempts - 1:
                raise
            cap = min(max_delay, base_delay * (2**attempt))
            sleeper(random.uniform(0, cap))
    assert last_error is not None
    raise last_error
