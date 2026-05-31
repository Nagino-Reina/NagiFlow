"""Conversation & chat endpoints (docs/05 §4.3).

Synchronous chat turn (text reply). Streaming (WebSocket), memory, and TTS land in P3/P5.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from ...schemas.conversation import (
    ConversationCreate,
    ConversationOut,
    MessageCreate,
    MessageOut,
    SendMessageResponse,
)
from ..deps import Conversations, CurrentPrincipal

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate, principal: CurrentPrincipal, svc: Conversations
) -> ConversationOut:
    conv = await svc.create(
        user_id=principal.user_id,
        character_id=body.character_id,
        is_guest=principal.kind != "user",
        title=body.title,
    )
    return ConversationOut.model_validate(conv)


@router.get("", response_model=list[ConversationOut])
async def list_conversations(
    principal: CurrentPrincipal, svc: Conversations
) -> list[ConversationOut]:
    convs = await svc.list_for_user(principal.user_id)
    return [ConversationOut.model_validate(c) for c in convs]


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
async def list_messages(
    conversation_id: str, principal: CurrentPrincipal, svc: Conversations
) -> list[MessageOut]:
    await svc.get_owned(conversation_id, principal.user_id)
    msgs = await svc.messages_for(conversation_id)
    return [MessageOut.model_validate(m) for m in msgs]


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
async def send_message(
    conversation_id: str, body: MessageCreate, principal: CurrentPrincipal, svc: Conversations
) -> SendMessageResponse:
    conv = await svc.get_owned(conversation_id, principal.user_id)
    user_msg, reply = await svc.send_message(conversation=conv, text=body.text)
    return SendMessageResponse(
        user_message=MessageOut.model_validate(user_msg),
        reply=MessageOut.model_validate(reply),
    )
