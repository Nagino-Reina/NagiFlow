"""Training data ORM models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nagiflow.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from nagiflow.models.character import Character
    from nagiflow.models.user import User


class TrainingDataset(Base, TimestampMixin):
    """A named collection of TTS training samples."""

    __tablename__ = "training_datasets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Optional: tie dataset to a specific character's voice
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Denormalized counters updated on item insert/delete
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    owner: Mapped["User"] = relationship("User")
    character: Mapped["Character | None"] = relationship("Character")
    items: Mapped[list["TrainingItem"]] = relationship(
        "TrainingItem",
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="TrainingItem.created_at",
    )


class TrainingItem(Base, TimestampMixin):
    """A single (text, audio) training pair."""

    __tablename__ = "training_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_datasets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Workspace-relative path to WAV file
    audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speaker_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # "generated" | "imported" | "recorded"
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="generated")
    # User quality rating 1-5, null = unrated
    quality_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    dataset: Mapped["TrainingDataset"] = relationship("TrainingDataset", back_populates="items")
