"""Conversation and message Pydantic schemas."""

from typing import Any
from uuid import UUID

from nagiflow.schemas.common import OrmBase, TimestampSchema


class ConversationCreate(OrmBase):
    character_id: UUID
    title: str | None = None


class ConversationResponse(TimestampSchema):
    id: UUID
    user_id: UUID
    character_id: UUID
    title: str | None


class MessageResponse(TimestampSchema):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    meta: dict[str, Any] | None
    audio_path: str | None


class ConversationDetail(ConversationResponse):
    messages: list[MessageResponse] = []


class ChatRequest(OrmBase):
    """One-shot (non-streaming) chat request body."""

    conversation_id: UUID | None = None
    message: str
    generate_audio: bool = False


class ChatResponse(OrmBase):
    conversation_id: UUID
    message: MessageResponse
    audio_url: str | None = None
