from __future__ import annotations

import logging

import pytest

from core.tracing import span


@pytest.fixture()
def logger():
    return logging.getLogger("test.tracing")


def test_span_yields_and_completes(logger):
    ran = []
    with span(logger, "test_op", job_id=1, provider="youtube", stage="fetch"):
        ran.append(True)
    assert ran == [True]


def test_span_without_provider(logger):
    ran = []
    with span(logger, "test_op"):
        ran.append(True)
    assert ran == [True]


def test_span_propagates_exception(logger):
    with pytest.raises(RuntimeError, match="boom"):
        with span(logger, "failing_op", job_id=2, provider="spotify"):
            raise RuntimeError("boom")


def test_span_with_correlation_id(logger):
    with span(logger, "test_op", job_id=3, correlation_id="abc-123"):
        pass
