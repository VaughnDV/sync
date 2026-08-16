from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

from core.logging import job_log
from core.metrics import provider_latency


@contextmanager
def span(
    logger,
    name: str,
    *,
    job_id: int | None = None,
    provider: str | None = None,
    stage: str | None = None,
    correlation_id: str | None = None,
) -> Iterator[None]:
    started = time.perf_counter()
    job_log(logger, f"span.start.{name}", job_id=job_id, provider=provider, stage=stage, correlation_id=correlation_id)
    try:
        yield
    finally:
        duration = time.perf_counter() - started
        if provider:
            provider_latency.labels(provider=provider, stage=stage or name).observe(duration)
        job_log(
            logger,
            f"span.end.{name}",
            job_id=job_id,
            provider=provider,
            stage=stage,
            duration_ms=round(duration * 1000, 1),
            correlation_id=correlation_id,
        )
