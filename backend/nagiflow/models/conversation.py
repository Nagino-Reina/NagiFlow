"""Conversation, ConversationParticipant, Message (docs/04 §5.5)."""

from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    character_id: Mapped[str] = mapped_column(String, index=True, nullable=False)  # primary
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    mode: Mapped[str] = mapped_column(String, default="chat", nullable=False)  # chat | live
    sensitive_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    director_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="active", nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)


class ConversationParticipant(Base, TimestampMixin):
    __tablename__ = "conversation_participant"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    character_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String, default="primary", nullable=False)
    join_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class Message(Base, TimestampMixin):
    __tablename__ = "message"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    speaker_character_id: Mapped[str | None] = mapped_column(String, nullable=True)
    in_reply_to_message_id: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
    media_asset_id: Mapped[str | None] = mapped_column(String, nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
