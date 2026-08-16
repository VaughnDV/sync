from __future__ import annotations

import pytest

from core.exceptions import TransientSyncError
from core.retry import retry_with_jitter


def test_success_on_first_attempt():
    calls = []

    def op():
        calls.append(1)
        return "ok"

    result = retry_with_jitter(op, attempts=3, sleeper=lambda _: None)
    assert result == "ok"
    assert len(calls) == 1


def test_retries_and_succeeds():
    results = iter(["fail", "fail", "ok"])
    attempts = []

    def op():
        val = next(results)
        attempts.append(val)
        if val != "ok":
            raise TransientSyncError("transient")
        return val

    result = retry_with_jitter(op, attempts=3, sleeper=lambda _: None)
    assert result == "ok"
    assert len(attempts) == 3


def test_raises_after_all_attempts_exhausted():
    def op():
        raise TransientSyncError("always fails")

    with pytest.raises(TransientSyncError):
        retry_with_jitter(op, attempts=3, sleeper=lambda _: None)


def test_non_transient_error_not_retried():
    calls = []

    def op():
        calls.append(1)
        raise ValueError("not transient")

    with pytest.raises(ValueError):
        retry_with_jitter(op, attempts=3, sleeper=lambda _: None)

    assert len(calls) == 1


def test_sleeper_called_between_retries():
    sleep_calls = []

    def op():
        raise TransientSyncError("fail")

    with pytest.raises(TransientSyncError):
        retry_with_jitter(op, attempts=3, sleeper=sleep_calls.append)

    assert len(sleep_calls) == 2
