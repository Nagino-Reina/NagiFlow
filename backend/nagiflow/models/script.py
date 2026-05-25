"""Script / Screenplay ORM models."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nagiflow.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from nagiflow.models.character import Character
    from nagiflow.models.user import User


class Script(Base, TimestampMixin):
    """A screenplay / dialogue script owned by a user."""

    __tablename__ = "scripts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    owner: Mapped["User"] = relationship("User")
    scenes: Mapped[list["ScriptScene"]] = relationship(
        "ScriptScene",
        back_populates="script",
        cascade="all, delete-orphan",
        order_by="ScriptScene.order",
    )


class ScriptScene(Base, TimestampMixin):
    """A scene within a script — a logical grouping of lines."""

    __tablename__ = "script_scenes"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    script_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False, default="Scene")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    script: Mapped["Script"] = relationship("Script", back_populates="scenes")
    lines: Mapped[list["ScriptLine"]] = relationship(
        "ScriptLine",
        back_populates="scene",
        cascade="all, delete-orphan",
        order_by="ScriptLine.order",
    )


class ScriptLine(Base, TimestampMixin):
    """A single dialogue line within a scene."""

    __tablename__ = "script_lines"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    scene_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("script_scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # nullable — stage directions have no character
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("characters.id", ondelete="SET NULL"), nullable=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Generated TTS output
    audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    scene: Mapped["ScriptScene"] = relationship("ScriptScene", back_populates="lines")
    character: Mapped["Character | None"] = relationship("Character")
