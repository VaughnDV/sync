from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PROMPT_VERSION = "song-classification/v1"
CONFIDENCE_THRESHOLD = 0.70


class ClassificationLabel(str, Enum):
    MUSIC = "music"
    NOT_MUSIC = "not_music"
    UNCERTAIN = "uncertain"


class SongClassification(BaseModel):
    """Trusted contract for classifier structured output."""

    model_config = ConfigDict(extra="forbid")

    classification: ClassificationLabel
    artist: str | None = None
    song: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("artist", "song", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        raise ValueError("artist and song must be strings")

    @model_validator(mode="after")
    def music_requires_identity(self) -> SongClassification:
        if self.classification is ClassificationLabel.MUSIC and (not self.artist or not self.song):
            raise ValueError("music classification requires artist and song")
        if self.classification is ClassificationLabel.NOT_MUSIC and self.confidence >= CONFIDENCE_THRESHOLD:
            return self
        return self

    def needs_human_review(self, threshold: float = CONFIDENCE_THRESHOLD) -> bool:
        if self.classification is ClassificationLabel.UNCERTAIN:
            return True
        if self.classification is ClassificationLabel.MUSIC and self.confidence < threshold:
            return True
        return False
