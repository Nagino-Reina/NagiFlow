"""Script & ScriptLine models (docs/04 §5.3-5.4, docs/07).

A script is an ordered set of lines; each line carries text, a speaker, optional timing, and
per-line **voice direction** (style / speech rate / reference clip / pause). Manual authoring
populates these directly; ASR import and render alignment fill timestamps later.
"""

from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Script(Base, TimestampMixin):
    __tablename__ = "script"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    language: Mapped[str] = mapped_column(String, default="en", nullable=False)
    # draft | review (post-ASR, pre-commit) | ready | archived
    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)
    source_kind: Mapped[str] = mapped_column(String, default="manual", nullable=False)
    default_character_id: Mapped[str | None] = mapped_column(String, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class ScriptLine(Base, TimestampMixin):
    __tablename__ = "script_line"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    script_id: Mapped[str] = mapped_column(
        String, ForeignKey("script.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    character_id: Mapped[str | None] = mapped_column(String, nullable=True)
    character_name_raw: Mapped[str | None] = mapped_column(String, nullable=True)
    text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    start_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_audio_key: Mapped[str | None] = mapped_column(String, nullable=True)
    style: Mapped[str | None] = mapped_column(Text, nullable=True)
    speech_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    pause_after_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    take: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
