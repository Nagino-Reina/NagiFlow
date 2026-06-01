"""AffectState — persistent mood per character↔partner relationship (docs/04 §5.9, docs/10).

One row per (character, partner). Holds the medium-term **mood** VAD and the last
short-term **emotion** VAD + discrete label; `updated_at` drives idle decay toward the
personality baseline (docs/10 §6/§8). Per-message emotion snapshots live in `message.meta`.
"""

from __future__ import annotations

from sqlalchemy import Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class AffectState(Base, TimestampMixin):
    __tablename__ = "affect_state"
    __table_args__ = (
        UniqueConstraint(
            "character_id", "user_id", "counterpart_character_id", name="uq_affect_relationship"
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    character_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    counterpart_character_id: Mapped[str | None] = mapped_column(String, nullable=True)

    # current mood VAD, each clamped to [-1, 1]
    mood_v: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mood_a: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mood_d: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # last emotion VAD + derived label/intensity
    emotion_v: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    emotion_a: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    emotion_d: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    emotion_label: Mapped[str] = mapped_column(String, default="neutral", nullable=False)
    emotion_intensity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
