"""Character Pydantic schemas."""

from typing import Any, Literal
from uuid import UUID

from pydantic import Field, field_validator

from nagiflow.schemas.common import OrmBase, TimestampSchema


class BigFivePersonality(OrmBase):
    """
    Big Five (OCEAN) personality trait scores.
    Each score is a float in [0, 100].
    """

    openness: float = Field(default=50.0, ge=0, le=100)
    conscientiousness: float = Field(default=50.0, ge=0, le=100)
    extraversion: float = Field(default=50.0, ge=0, le=100)
    agreeableness: float = Field(default=50.0, ge=0, le=100)
    neuroticism: float = Field(default=50.0, ge=0, le=100)


class PersonalityConfig(OrmBase):
    big_five: BigFivePersonality = Field(default_factory=BigFivePersonality)
    custom: dict[str, Any] = Field(default_factory=dict)


class CharacterCreate(OrmBase):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None
    system_prompt: str | None = None
    personality: PersonalityConfig | None = None

    # LLM / TTS overrides
    llm_provider: str | None = None
    llm_model: str | None = None
    tts_provider: str | None = None
    tts_speaker_id: int | None = None

    # Model type: live2d or 3d
    model_type: Literal["live2d", "3d"] | None = None
    is_public: bool = False


class CharacterUpdate(OrmBase):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    system_prompt: str | None = None
    personality: PersonalityConfig | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    tts_provider: str | None = None
    tts_speaker_id: int | None = None
    model_type: Literal["live2d", "3d"] | None = None
    is_public: bool | None = None


class CharacterResponse(TimestampSchema):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    system_prompt: str | None
    personality: dict[str, Any] | None
    llm_provider: str | None
    llm_model: str | None
    tts_provider: str | None
    tts_speaker_id: int | None
    avatar_path: str | None
    voice_sample_path: str | None
    model_path: str | None
    model_type: str | None
    is_public: bool


class CharacterBrief(OrmBase):
    """Lightweight character summary for list endpoints."""

    id: UUID
    name: str
    description: str | None
    avatar_path: str | None
    model_type: str | None
    is_public: bool
