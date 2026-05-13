"""Conversation management and one-shot chat endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import PaginationParams, get_current_active_user
from nagiflow.core.database import get_session
from nagiflow.models.user import User
from nagiflow.schemas.common import MessageResponse
from nagiflow.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationDetail,
    ConversationResponse,
    MessageResponse as MsgSchema,
)
from nagiflow.services.conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ConversationResponse:
    """Create a new conversation with a character."""
    svc = ConversationService(db)
    conv = await svc.create(current_user.id, data)
    return ConversationResponse.model_validate(conv)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    character_id: UUID | None = Query(default=None),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[ConversationResponse]:
    """List conversations for the current user."""
    svc = ConversationService(db)
    convs = await svc.list_for_user(
        current_user.id,
        character_id=character_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [ConversationResponse.model_validate(c) for c in convs]


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ConversationDetail:
    """Retrieve a conversation and its message history."""
    svc = ConversationService(db)
    conv = await svc.get(conversation_id, current_user.id)
    messages = [MsgSchema.model_validate(m) for m in conv.messages]
    detail = ConversationDetail.model_validate(conv)
    detail.messages = messages
    return detail


@router.delete("/{conversation_id}", response_model=MessageResponse)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a conversation and all its messages."""
    svc = ConversationService(db)
    await svc.delete(conversation_id, current_user.id)
    return MessageResponse(message="Conversation deleted.")


# ---------------------------------------------------------------------------
# One-shot chat (non-streaming)
# ---------------------------------------------------------------------------


@router.post("/characters/{character_id}/chat", response_model=ChatResponse)
async def chat(
    character_id: UUID,
    req: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """
    Send a message to a character and receive a complete response.

    For streaming responses, use the ``/ws/stream`` WebSocket endpoint.
    If ``generate_audio`` is true, the response includes an ``audio_url``
    pointing to the synthesised WAV file.
    """
    svc = ConversationService(db)
    conv, msg, audio_url = await svc.chat(
        conversation_id=req.conversation_id,
        user_id=current_user.id,
        character_id=character_id,
        user_message=req.message,
        generate_audio=req.generate_audio,
    )
    return ChatResponse(
        conversation_id=conv.id,
        message=MsgSchema.model_validate(msg),
        audio_url=audio_url,
    )


@router.post("/characters/{character_id}/tts", response_model=MessageResponse)
async def generate_tts(
    character_id: UUID,
    text: str = Query(..., min_length=1, max_length=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """
    Generate TTS audio for arbitrary text using a character's voice settings.
    Returns a URL to the cached audio file.
    """
    from nagiflow.services.character import CharacterService
    from nagiflow.tts import TTSConfig, get_tts_provider
    from nagiflow.core.workspace import workspace
    import uuid as _uuid

    char_svc = CharacterService(db)
    character = await char_svc.get(character_id, current_user.id)

    from nagiflow.config import settings

    provider = get_tts_provider(character.tts_provider or settings.DEFAULT_TTS_PROVIDER)
    speaker_id = character.tts_speaker_id or settings.DEFAULT_VOICEVOX_SPEAKER
    config = TTSConfig(speaker_id=speaker_id)
    result = await provider.synthesize(text, config)

    filename = f"{_uuid.uuid4()}.wav"
    dest = workspace.audio_cache_dir() / str(character_id) / filename
    await workspace.save_file(dest, result.audio_bytes)
    url = f"/api/v1/audio/{workspace.relative_to_workspace(dest)}"
    return MessageResponse(message=url)
