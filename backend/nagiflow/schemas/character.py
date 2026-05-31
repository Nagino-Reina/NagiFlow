"""Character schemas (docs/05 §4.1, docs/08)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

Trait = Field(ge=0, le=100)


class BigFive(BaseModel):
    openness: int = Trait
    conscientiousness: int = Trait
    extraversion: int = Trait
    agreeableness: int = Trait
    neuroticism: int = Trait


class CharacterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    persona: str = ""
    big_five: BigFive = Field(default_factory=BigFive)
    default_language: str = "en"
    aliases: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    guest_visible: bool = False
    avatar_renderer: str | None = None


class CharacterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    persona: str | None = None
    big_five: BigFive | None = None
    default_language: str | None = None
    aliases: list[str] | None = None
    tags: list[str] | None = None
    guest_visible: bool | None = None
    avatar_renderer: str | None = None
    status: str | None = None


class CharacterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    aliases: list[str]
    description: str
    persona: str
    big_five: dict
    default_language: str
    guest_visible: bool
    avatar_renderer: str | None
    status: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime
