from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from django.utils import timezone
from openai import APITimeoutError, RateLimitError

from core.exceptions import AIInvalidSchema, AIRateLimited, AIRefusal, AITimeout, BudgetExceeded
from providers.classifier import LiveSongClassifier
from providers.interfaces import YoutubeVideo
from providers.schemas import PROMPT_VERSION, SongClassification


def _parsed() -> SongClassification:
    return SongClassification(classification="music", artist="Adele", song="Hello", confidence=0.98)


def _completion(*, parsed=None, content="", refusal=None, tokens=100):
    message = SimpleNamespace(parsed=parsed, content=content, refusal=refusal)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)], usage=SimpleNamespace(total_tokens=tokens))


def _client_with(completion):
    client = MagicMock()
    client.chat.completions.parse.return_value = completion
    return client


def test_live_classifier_returns_structured_result():
    client = _client_with(_completion(parsed=_parsed(), tokens=200))
    classifier = LiveSongClassifier(client=client, model="test-model", cost_budget_usd=1)

    result = classifier.classify(YoutubeVideo("v1", "Adele - Hello"))

    assert result.classification == "music"
    assert result.artist == "Adele"
    assert result.song == "Hello"
    assert result.tokens_used == 200
    assert result.model == "test-model"
    assert result.prompt_version == PROMPT_VERSION
    assert result.estimated_cost_usd > 0
    client.chat.completions.parse.assert_called_once()


def test_live_classifier_validates_json_fallback():
    content = _parsed().model_dump_json()
    classifier = LiveSongClassifier(client=_client_with(_completion(content=content)), cost_budget_usd=1)
    result = classifier.classify(YoutubeVideo("v1", "Adele - Hello"))
    assert result.confidence == 0.98


def test_live_classifier_rejects_refusal_and_invalid_json():
    classifier = LiveSongClassifier(client=_client_with(_completion(refusal="no")), cost_budget_usd=1)
    with pytest.raises(AIRefusal):
        classifier.classify(YoutubeVideo("v1", "title"))

    classifier = LiveSongClassifier(client=_client_with(_completion(content="not-json")), cost_budget_usd=1)
    with pytest.raises(AIInvalidSchema):
        classifier.classify(YoutubeVideo("v1", "title"))


def test_live_classifier_maps_openai_transient_errors():
    request = httpx.Request("POST", "https://api.openai.test")
    client = MagicMock()
    client.chat.completions.parse.side_effect = APITimeoutError(request=request)
    with pytest.raises(AITimeout):
        LiveSongClassifier(client=client, cost_budget_usd=1).classify(YoutubeVideo("v1", "title"))

    response = httpx.Response(429, request=request)
    client.chat.completions.parse.side_effect = RateLimitError("limited", response=response, body=None)
    with pytest.raises(AIRateLimited):
        LiveSongClassifier(client=client, cost_budget_usd=1).classify(YoutubeVideo("v1", "title"))


def test_live_classifier_enforces_budget_before_and_after_request():
    classifier = LiveSongClassifier(client=MagicMock(), cost_budget_usd=0)
    with pytest.raises(BudgetExceeded):
        classifier.classify(YoutubeVideo("v1", "title"))

    client = _client_with(_completion(parsed=_parsed(), tokens=1000))
    classifier = LiveSongClassifier(client=client, cost_budget_usd=0.00001)
    with pytest.raises(BudgetExceeded):
        classifier.classify(YoutubeVideo("v1", "title"))


def test_live_classifier_reads_valid_cache():
    row = SimpleNamespace(
        payload={"classification": "music", "artist": "Adele", "song": "Hello", "confidence": 0.9},
        classifier_version=PROMPT_VERSION,
    )
    cache_model = MagicMock()
    cache_model.objects.filter.return_value.first.return_value = row
    client = MagicMock()
    classifier = LiveSongClassifier(client=client, model="cached-model", cost_budget_usd=1, cache_model=cache_model)

    result = classifier.classify(YoutubeVideo("v1", "  Adele   - HELLO "))

    assert result.cached is True
    assert result.model == "cached-model"
    client.chat.completions.parse.assert_not_called()


def test_live_classifier_writes_cache():
    cache_model = MagicMock()
    cache_model.objects.filter.return_value.first.return_value = None
    classifier = LiveSongClassifier(
        client=_client_with(_completion(parsed=_parsed())),
        cost_budget_usd=1,
        cache_model=cache_model,
    )
    video = YoutubeVideo("v1", "  Adele   - HELLO ")

    classifier.classify(video)

    cache_model.objects.update_or_create.assert_called_once()
    _, kwargs = cache_model.objects.update_or_create.call_args
    assert kwargs["defaults"]["normalised_title"] == "adele - hello"
    assert kwargs["defaults"]["expires_at"] > timezone.now() + timedelta(days=1)


def test_cache_key_is_stable_for_whitespace_and_case():
    classifier = LiveSongClassifier(client=MagicMock(), cost_budget_usd=1)
    first = classifier._cache_key(YoutubeVideo("v1", " Adele   - Hello "))
    second = classifier._cache_key(YoutubeVideo("v1", "adele - hello"))
    assert first == second
