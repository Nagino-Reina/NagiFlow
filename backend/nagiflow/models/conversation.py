"""Conversation and Message ORM models."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from nagiflow.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from nagiflow.models.character import Character
    from nagiflow.models.user import User


class Conversation(Base, TimestampMixin):
    """A conversation session between a user and a character."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    character: Mapped["Character"] = relationship("Character", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base, TimestampMixin):
    """A single message within a conversation (user or assistant turn)."""

    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # "user" | "assistant" | "system" | "tool"
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional structured metadata: token counts, tool calls, emotion tags, etc.
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # TTS audio path (workspace-relative) if audio was generated for this message
    audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    conversation: Mapped[Conversation] = relationship("Conversation", back_populates="messages")
