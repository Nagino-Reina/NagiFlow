"""
Conversation service.

Orchestrates the full message pipeline:
  1. Load conversation history
  2. Retrieve relevant memories and knowledge (RAG)
  3. Build CharacterAgent and generate LLM response
  4. Persist assistant message
  5. Optionally synthesise TTS audio
  6. Optionally ingest memorable facts into long-term memory
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nagiflow.core.exceptions import NotFoundError, PermissionDeniedError
from nagiflow.core.workspace import workspace
from nagiflow.models.conversation import Conversation, Message
from nagiflow.plugin.base import LLMMessage, TTSConfig
from nagiflow.plugin.registry import registry
from nagiflow.schemas.conversation import ConversationCreate
from nagiflow.services.agent import CharacterAgent
from nagiflow.services.character import CharacterService
from nagiflow.services.knowledge import KnowledgeService
from nagiflow.services.memory import MemoryService

_HISTORY_WINDOW = 20  # number of recent messages to include in LLM context


class ConversationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._memory_svc = MemoryService(db)
        self._knowledge_svc = KnowledgeService(db)
        self._character_svc = CharacterService(db)

    # ------------------------------------------------------------------
    # Conversation CRUD
    # ------------------------------------------------------------------

    async def create(self, user_id: UUID, data: ConversationCreate) -> Conversation:
        await self._character_svc.get(data.character_id, user_id)  # access check
        conv = Conversation(
            user_id=user_id,
            character_id=data.character_id,
            title=data.title,
        )
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    async def get(self, conversation_id: UUID, user_id: UUID) -> Conversation:
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if conv is None:
            raise NotFoundError(f"Conversation '{conversation_id}' not found.")
        if conv.user_id != user_id:
            raise PermissionDeniedError()
        return conv

    async def list_for_user(
        self, user_id: UUID, character_id: UUID | None = None, limit: int = 50, offset: int = 0
    ) -> list[Conversation]:
        stmt = select(Conversation).where(Conversation.user_id == user_id)
        if character_id:
            stmt = stmt.where(Conversation.character_id == character_id)
        stmt = stmt.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, conversation_id: UUID, user_id: UUID) -> None:
        conv = await self.get(conversation_id, user_id)
        await self.db.delete(conv)

    # ------------------------------------------------------------------
    # Message helpers
    # ------------------------------------------------------------------

    async def _get_recent_messages(self, conversation_id: UUID) -> list[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(_HISTORY_WINDOW)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def _add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        meta: dict | None = None,
        audio_path: str | None = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta=meta,
            audio_path=audio_path,
        )
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg

    # ------------------------------------------------------------------
    # Core chat pipeline
    # ------------------------------------------------------------------

    async def _build_agent(self, character_id: UUID, user_id: UUID) -> CharacterAgent:
        character = await self._character_svc.get(character_id, user_id)
        char_skills = await self._character_svc.get_skills(character_id, user_id)
        skill_instances = registry.instantiate_skills_for_character(
            skill_names=[cs.skill.name for cs in char_skills],
            configs={cs.skill.name: cs.config for cs in char_skills if cs.config},
        )
        return CharacterAgent(character=character, skills=skill_instances)

    async def chat(
        self,
        conversation_id: UUID | None,
        user_id: UUID,
        character_id: UUID,
        user_message: str,
        generate_audio: bool = False,
    ) -> tuple[Conversation, Message, str | None]:
        """
        One-shot chat.  Returns (conversation, assistant_message, audio_url_or_none).
        """
        # Ensure conversation exists
        if conversation_id is None:
            conv = await self.create(user_id, ConversationCreate(character_id=character_id))
        else:
            conv = await self.get(conversation_id, user_id)

        # Persist user message
        await self._add_message(conv.id, "user", user_message)

        # Build context
        memory_ctx = await self._memory_svc.format_context(
            conv.character_id, user_id, user_message
        )
        knowledge_ctx = await self._knowledge_svc.format_context(
            user_id, user_message, character_id=conv.character_id
        )

        # Build LLM history
        recent = await self._get_recent_messages(conv.id)
        llm_history = [
            LLMMessage(role=m.role, content=m.content)
            for m in recent
            if m.role in ("user", "assistant")
        ]

        # Generate response
        agent = await self._build_agent(conv.character_id, user_id)
        response = await agent.generate(
            history=llm_history,
            user_message=user_message,
            memory_context=memory_ctx,
            knowledge_context=knowledge_ctx,
        )

        # Synthesise TTS if requested
        audio_url: str | None = None
        audio_path: str | None = None
        if generate_audio:
            audio_path, audio_url = await self._synthesize_audio(
                response.content, agent.character
            )

        # Persist assistant message
        assistant_msg = await self._add_message(
            conv.id,
            "assistant",
            response.content,
            meta={
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "model": response.model,
            },
            audio_path=audio_path,
        )

        # Background: try to ingest memorable content
        await self._memory_svc.ingest_from_message(
            conv.character_id, user_id, user_message, importance=4.0
        )

        return conv, assistant_msg, audio_url

    async def stream_chat(
        self,
        conversation_id: UUID | None,
        user_id: UUID,
        character_id: UUID,
        user_message: str,
    ) -> AsyncGenerator[tuple[str, UUID | None], None]:
        """
        Streaming chat.  Yields (text_delta, conversation_id_on_first_chunk).

        The conversation_id is yielded once (on the first chunk) so the
        caller can associate subsequent chunks with the correct conversation.
        """
        # Ensure conversation
        if conversation_id is None:
            conv = await self.create(user_id, ConversationCreate(character_id=character_id))
        else:
            conv = await self.get(conversation_id, user_id)

        await self._add_message(conv.id, "user", user_message)

        memory_ctx = await self._memory_svc.format_context(
            conv.character_id, user_id, user_message
        )
        knowledge_ctx = await self._knowledge_svc.format_context(
            user_id, user_message, character_id=conv.character_id
        )

        recent = await self._get_recent_messages(conv.id)
        llm_history = [
            LLMMessage(role=m.role, content=m.content)
            for m in recent
            if m.role in ("user", "assistant")
        ]

        agent = await self._build_agent(conv.character_id, user_id)

        full_response = ""
        first = True
        async for chunk in agent.stream(
            history=llm_history,
            user_message=user_message,
            memory_context=memory_ctx,
            knowledge_context=knowledge_ctx,
        ):
            full_response += chunk
            if first:
                yield chunk, conv.id
                first = False
            else:
                yield chunk, None

        # Persist completed assistant message
        await self._add_message(
            conv.id, "assistant", full_response, meta={"model": agent._model}
        )
        await self._memory_svc.ingest_from_message(
            conv.character_id, user_id, user_message, importance=4.0
        )

    # ------------------------------------------------------------------
    # TTS synthesis
    # ------------------------------------------------------------------

    async def _synthesize_audio(
        self, text: str, character: object
    ) -> tuple[str, str]:
        """Synthesise audio for *text* and return (workspace_rel_path, url_path)."""
        from nagiflow.config import settings

        tts_provider_name = getattr(character, "tts_provider", None) or settings.DEFAULT_TTS_PROVIDER
        speaker_id = getattr(character, "tts_speaker_id", None) or settings.DEFAULT_VOICEVOX_SPEAKER
        char_id = getattr(character, "id", "unknown")

        provider = registry.get_tts(tts_provider_name)
        config = TTSConfig(speaker_id=speaker_id)
        result = await provider.synthesize(text, config)

        filename = f"{uuid.uuid4()}.wav"
        dest = workspace.audio_cache_dir() / str(char_id) / filename
        await workspace.save_file(dest, result.audio_bytes)
        rel = workspace.relative_to_workspace(dest)
        url = f"/api/v1/audio/{rel}"
        return rel, url

    async def stream_tts_with_llm(
        self,
        conversation_id: UUID | None,
        user_id: UUID,
        character_id: UUID,
        user_message: str,
    ) -> AsyncGenerator[bytes, None]:
        """
        Concurrent LLM streaming + sentence-level TTS synthesis.

        Yields raw WAV audio chunks as each sentence is completed by the LLM
        and immediately synthesised.  Designed for WebSocket delivery.
        """
        from nagiflow.config import settings

        if conversation_id is None:
            conv = await self.create(user_id, ConversationCreate(character_id=character_id))
        else:
            conv = await self.get(conversation_id, user_id)

        await self._add_message(conv.id, "user", user_message)

        memory_ctx = await self._memory_svc.format_context(conv.character_id, user_id, user_message)
        knowledge_ctx = await self._knowledge_svc.format_context(user_id, user_message, character_id=conv.character_id)

        recent = await self._get_recent_messages(conv.id)
        llm_history = [LLMMessage(role=m.role, content=m.content) for m in recent if m.role in ("user", "assistant")]

        agent = await self._build_agent(conv.character_id, user_id)
        character = agent.character
        tts_provider_name = character.tts_provider or settings.DEFAULT_TTS_PROVIDER
        speaker_id = character.tts_speaker_id or settings.DEFAULT_VOICEVOX_SPEAKER

        tts = registry.get_tts(tts_provider_name)
        tts_config = TTSConfig(speaker_id=speaker_id)

        sentence_buffer = ""
        full_text = ""
        import re
        sentence_end = re.compile(r"[.!?。！？]\s*")

        async for chunk in agent.stream(
            history=llm_history,
            user_message=user_message,
            memory_context=memory_ctx,
            knowledge_context=knowledge_ctx,
        ):
            full_text += chunk
            sentence_buffer += chunk

            # When a sentence boundary is detected, synthesise and yield
            while sentence_end.search(sentence_buffer):
                match = sentence_end.search(sentence_buffer)
                if match is None:
                    break
                sentence = sentence_buffer[: match.end()].strip()
                sentence_buffer = sentence_buffer[match.end() :]
                if sentence:
                    result = await tts.synthesize(sentence, tts_config)
                    if result.audio_bytes:
                        yield result.audio_bytes

        # Synthesise any remaining text
        if sentence_buffer.strip():
            result = await tts.synthesize(sentence_buffer.strip(), tts_config)
            if result.audio_bytes:
                yield result.audio_bytes

        await self._add_message(conv.id, "assistant", full_text, meta={"model": agent._model})
        await self._memory_svc.ingest_from_message(conv.character_id, user_id, user_message)
