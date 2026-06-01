"""UsageRecord — per-call token/audio accounting (docs/04 §5, docs/12 §3).

One row per model/provider call (LLM reply, TTS synthesis, later embedding/ASR). Aggregated
for totals and per-character / per-provider / per-day breakdowns (FR-OBS-3). Local providers
have no cost, so token counts are primarily capacity signals until a paid provider is used.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, _utcnow


class UsageRecord(Base):
    __tablename__ = "usage_record"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # llm | embedding | tts | asr
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    character_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    conversation_id: Mapped[str | None] = mapped_column(String, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    est_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, index=True, nullable=False
    )
    correlation_id: Mapped[str | None] = mapped_column(String, nullable=True)
