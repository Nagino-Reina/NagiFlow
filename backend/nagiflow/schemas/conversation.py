"""Conversation & message schemas (docs/05 §4.3)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    character_id: str
    title: str | None = None


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    character_id: str
    user_id: str
    mode: str
    sensitive_mode: bool
    title: str | None
    status: str
    created_at: datetime


class MessageCreate(BaseModel):
    text: str = Field(min_length=1)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    speaker_character_id: str | None
    content: str
    created_at: datetime


class SendMessageResponse(BaseModel):
    user_message: MessageOut
    reply: MessageOut
