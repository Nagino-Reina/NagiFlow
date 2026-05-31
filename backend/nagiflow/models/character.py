"""Character & VoiceModel models (docs/04 §5.2)."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


def _default_big_five() -> dict:
    return {
        "openness": 50,
        "conscientiousness": 50,
        "extraversion": 50,
        "agreeableness": 50,
        "neuroticism": 50,
    }


class Character(Base, TimestampMixin):
    __tablename__ = "character"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    aliases: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    persona: Mapped[str] = mapped_column(Text, default="", nullable=False)
    big_five: Mapped[dict] = mapped_column(JSON, default=_default_big_five, nullable=False)
    default_language: Mapped[str] = mapped_column(String, default="en", nullable=False)
    default_voice_model_id: Mapped[str | None] = mapped_column(String, nullable=True)
    default_style: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    portrait_key: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_bundle_key: Mapped[str | None] = mapped_column(String, nullable=True)
    avatar_renderer: Mapped[str | None] = mapped_column(String, nullable=True)
    guest_visible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)


class VoiceModel(Base, TimestampMixin):
    __tablename__ = "voice_model"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    character_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # zero_shot|voice_design|fine_tuned
    provider: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    reference_keys: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    design_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_key: Mapped[str | None] = mapped_column(String, nullable=True)
    params: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String, default="ready", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
