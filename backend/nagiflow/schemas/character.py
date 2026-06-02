"""Character schemas (docs/05 §4.1, docs/08)."""

from __future__ import annotations

from datetime import datetime

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# Each trait defaults to the neutral midpoint so `big_five` is optional on create.
Trait = Annotated[int, Field(ge=0, le=100)]


class BigFive(BaseModel):
    openness: Trait = 50
    conscientiousness: Trait = 50
    extraversion: Trait = 50
    agreeableness: Trait = 50
    neuroticism: Trait = 50


class ParamFormulaOut(BaseModel):
    """A continuous parameter as `base + Σ coefficients[trait] * norm(score)`, clamped."""

    base: float
    coefficients: dict[str, float]
    min: float
    max: float


class PersonalitySchemaOut(BaseModel):
    """The complete Big Five → behavior mapping spec (docs/08 §3.2).

    Served once; the client computes the per-profile view locally from this, so adjusting
    sliders triggers no further requests (FR-CM-4, NFR-MAINT-2).
    """

    bands: list[str]
    thresholds: list[int]
    traits: list[str]
    directives: dict[str, list[str]]
    verbosity: list[str]
    expressiveness: list[str]
    voice_style: dict[str, dict[str, str]]
    params: dict[str, ParamFormulaOut]


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
    has_portrait: bool
    created_at: datetime
    updated_at: datetime
