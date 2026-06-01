"""Conversation service — create + synchronous chat turn (docs/05 §4.3, FR-RT-1)."""

from __future__ import annotations

from ..core import errors
from ..core.ids import new_id
from ..core.logging import get_correlation_id
from ..models.character import Character
from ..models.conversation import Conversation, ConversationParticipant, Message
from ..providers.registry import ProviderRegistry
from ..repositories.characters import CharacterRepository
from ..repositories.conversations import ConversationRepository, MessageRepository
from . import personality
from .affect import AffectService
from .media_service import MediaService
from .orchestrator import DialogueOrchestrator
from .usage_service import UsageService
from .voice_service import VoiceService


def _style_hint(character: Character, affect_tags: list[str]) -> str | None:
    """Merge personality voice-style tags with the turn's affect tags (docs/10 §7.2)."""
    seen: set[str] = set()
    tags: list[str] = []
    for tag in (*personality.resolve(character.big_five).voice_style, *affect_tags):
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return ", ".join(tags) or None


def _reply_rate(character: Character, rate_delta: float) -> float:
    """Personality speech rate nudged by affect, clamped to the personality band (docs/10 §7.2)."""
    rate = personality.resolve(character.big_five).speech_rate + rate_delta
    return max(0.85, min(1.15, rate))


class ConversationService:
    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
        characters: CharacterRepository,
        registry: ProviderRegistry,
        affect: AffectService,
        voice: VoiceService,
        media: MediaService,
        usage: UsageService,
        *,
        synthesize_replies: bool = True,
    ) -> None:
        self.conversations = conversations
        self.messages = messages
        self.characters = characters
        self.registry = registry
        self.affect = affect
        self.voice = voice
        self.media = media
        self.usage = usage
        self.synthesize_replies = synthesize_replies

    async def create(
        self, *, user_id: str, character_id: str, is_guest: bool, title: str | None
    ) -> Conversation:
        character = await self.characters.get(character_id)
        if character is None or character.status == "archived":
            raise errors.not_found("character", character_id)
        if is_guest and not character.guest_visible:
            # guests may only converse with guest-visible characters (docs/09 §3)
            raise errors.guest_upgrade_required()
        conv = Conversation(
            id=new_id("conv"),
            character_id=character_id,
            user_id=user_id,
            mode="chat",
            sensitive_mode=False,
            title=title,
            status="active",
        )
        self.conversations.add(conv)
        participant = ConversationParticipant(
            id=new_id("cp"),
            conversation_id=conv.id,
            character_id=character_id,
            role="primary",
            join_order=0,
        )
        self.conversations.s.add(participant)
        # Flush so server/Python defaults (id wiring, created_at) populate before the
        # response is serialized — the request's commit runs only at dependency teardown.
        await self.conversations.s.flush()
        return conv

    async def get_owned(self, conversation_id: str, user_id: str) -> Conversation:
        conv = await self.conversations.get(conversation_id)
        if conv is None:
            raise errors.not_found("conversation", conversation_id)
        if conv.user_id != user_id:
            raise errors.forbidden(message="Not your conversation.")
        return conv

    async def list_for_user(self, user_id: str) -> list[Conversation]:
        return await self.conversations.list_for_user(user_id)

    async def messages_for(self, conversation_id: str) -> list[Message]:
        return await self.messages.list_for_conversation(conversation_id)

    async def send_message(
        self, *, conversation: Conversation, text: str
    ) -> tuple[Message, Message]:
        character = await self.characters.get(conversation.character_id)
        if character is None:
            raise errors.not_found("character", conversation.character_id)

        history = await self.messages.list_for_conversation(conversation.id)

        user_msg = Message(
            id=new_id("msg"),
            conversation_id=conversation.id,
            role="user",
            content=text,
        )
        self.messages.add(user_msg)

        # Emotion: appraise the turn and update the per-relationship mood (docs/10 §3, §6).
        affect_result = await self.affect.process_turn(
            character=character,
            user_id=conversation.user_id,
            user_text=text,
            history=history,
        )

        orchestrator = DialogueOrchestrator(self.registry)
        result = await orchestrator.handle_turn(
            character=character,
            history=history,
            user_text=text,
            affect_directive=affect_result.directive,
        )

        reply_msg = Message(
            id=new_id("msg"),
            conversation_id=conversation.id,
            role="character",
            speaker_character_id=character.id,
            in_reply_to_message_id=user_msg.id,
            content=result.text or "…",
            meta={
                "usage": {
                    "prompt_tokens": result.usage.prompt_tokens if result.usage else None,
                    "completion_tokens": (
                        result.usage.completion_tokens if result.usage else None
                    ),
                },
                "affect": affect_result.affect.to_dict(),
                "expression": affect_result.expression,
                "voice_style": affect_result.voice_style,
            },
        )
        self.messages.add(reply_msg)
        # Flush so both messages' created_at populate before serialization (see create()).
        await self.messages.s.flush()

        correlation_id = get_correlation_id()
        # Account for the reply's LLM call (FR-OBS-3, docs/12 §3).
        await self.usage.record(
            kind="llm",
            provider=result.provider,
            model=result.model,
            user_id=conversation.user_id,
            character_id=character.id,
            conversation_id=conversation.id,
            prompt_tokens=result.usage.prompt_tokens if result.usage else None,
            completion_tokens=result.usage.completion_tokens if result.usage else None,
            correlation_id=correlation_id,
        )

        # Synthesize reply audio for playback (docs/11 §4.6). Best-effort: a TTS failure
        # leaves media_asset_id null and never blocks the text reply.
        if self.synthesize_replies and result.text:
            audio = await self.voice.synthesize_reply(
                character,
                text=reply_msg.content,
                style=_style_hint(character, affect_result.voice_style),
                speech_rate=_reply_rate(character, affect_result.speech_rate_delta),
            )
            if audio:
                asset = await self.media.store_message_audio(
                    message_id=reply_msg.id, audio=audio
                )
                reply_msg.media_asset_id = asset.id
                await self.messages.s.flush()
                await self.usage.record(
                    kind="tts",
                    provider=self.registry.get_tts().name,
                    user_id=conversation.user_id,
                    character_id=character.id,
                    conversation_id=conversation.id,
                    audio_seconds=(asset.duration_ms or 0) / 1000.0,
                    correlation_id=correlation_id,
                )
        return user_msg, reply_msg
