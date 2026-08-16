import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from providers.schemas import PROMPT_VERSION, SongClassification
from providers.fakes import FakeSongClassifier
from providers.interfaces import YoutubeVideo
from core.exceptions import AIInvalidSchema, AIRefusal, AITimeout


FIXTURES = json.loads(
    (Path(__file__).resolve().parents[2] / "src/providers/fixtures/classifier_samples.json").read_text()
)


def test_valid_music_schema():
    parsed = SongClassification.model_validate(FIXTURES["valid_music"])
    assert parsed.classification.value == "music"
    assert parsed.artist == "Adele"
    assert not parsed.needs_human_review()


def test_not_music_schema():
    parsed = SongClassification.model_validate(FIXTURES["not_music"])
    assert parsed.classification.value == "not_music"


def test_low_confidence_needs_review():
    parsed = SongClassification.model_validate(FIXTURES["low_confidence"])
    assert parsed.needs_human_review()


def test_missing_fields_rejected():
    with pytest.raises(ValidationError):
        SongClassification.model_validate(FIXTURES["missing_fields"])


def test_contradictory_music_without_identity():
    with pytest.raises(ValidationError):
        SongClassification.model_validate(FIXTURES["contradictory"])


def test_malformed_json_rejected():
    with pytest.raises(ValidationError):
        SongClassification.model_validate_json(FIXTURES["malformed"])


def test_fake_classifier_timeout_and_refusal():
    classifier = FakeSongClassifier(timeout_ids=["t1"], refusal_ids=["r1"], malformed_ids=["m1"])
    with pytest.raises(AITimeout):
        classifier.classify(YoutubeVideo("t1", "title"))
    with pytest.raises(AIRefusal):
        classifier.classify(YoutubeVideo("r1", "title"))
    with pytest.raises(AIInvalidSchema):
        classifier.classify(YoutubeVideo("m1", "title"))


def test_prompt_version_constant():
    assert PROMPT_VERSION.startswith("song-classification/")
