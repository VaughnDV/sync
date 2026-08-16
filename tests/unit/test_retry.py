from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from core.exceptions import TransientSyncError
from core.retry import retry_with_jitter


def test_retry_returns_on_first_success():
    operation = MagicMock(return_value="ok")
    sleeper = MagicMock()
    assert retry_with_jitter(operation, attempts=3, sleeper=sleeper) == "ok"
    operation.assert_called_once()
    sleeper.assert_not_called()


def test_retry_sleeps_then_succeeds(monkeypatch):
    operation = MagicMock(side_effect=[TransientSyncError(), "ok"])
    sleeper = MagicMock()
    monkeypatch.setattr("core.retry.random.uniform", MagicMock(return_value=0.1))
    assert retry_with_jitter(operation, attempts=3, sleeper=sleeper) == "ok"
    sleeper.assert_called_once_with(0.1)


def test_retry_reraises_last_transient_error():
    operation = MagicMock(side_effect=TransientSyncError("still down"))
    with pytest.raises(TransientSyncError, match="still down"):
        retry_with_jitter(operation, attempts=2, sleeper=MagicMock())
    assert operation.call_count == 2


def test_retry_does_not_catch_non_transient_errors():
    operation = MagicMock(side_effect=ValueError("bad input"))
    with pytest.raises(ValueError, match="bad input"):
        retry_with_jitter(operation, sleeper=MagicMock())
    operation.assert_called_once()
