from __future__ import annotations

import json
import logging
from typing import Any


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        extra = getattr(record, "sync", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, default=str)


def job_log(
    logger: logging.Logger,
    event: str,
    *,
    job_id: int | None = None,
    provider: str | None = None,
    stage: str | None = None,
    attempt: int | None = None,
    duration_ms: float | None = None,
    request_id: str | None = None,
    correlation_id: str | None = None,
    error_code: str | None = None,
    **fields: Any,
) -> None:
    """Emit a structured log line without tokens or unnecessary user content."""
    payload = {
        "event": event,
        "job_id": job_id,
        "provider": provider,
        "stage": stage,
        "attempt": attempt,
        "duration_ms": duration_ms,
        "request_id": request_id,
        "correlation_id": correlation_id,
        "error_code": error_code,
    }
    payload.update(fields)
    logger.info(
        event,
        extra={"sync": {key: value for key, value in payload.items() if value is not None}},
    )
