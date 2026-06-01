"""Conversation service — create + synchronous chat turn (docs/05 §4.3, FR-RT-1)."""

from __future__ import annotations

from ..core import errors
from ..core.ids import new_id
from ..models.conversation import Conversation, ConversationParticipant, Message
from ..providers.registry import ProviderRegistry
from ..repositories.characters import CharacterRepository
from ..repositories.conversations import ConversationRepository, MessageRepository
from .affect import AffectService
from .orchestrator import DialogueOrchestrator


class ConversationService:
    def __init__(
        self,
        conversations: ConversationRepository,
        messages: MessageRepository,
        characters: CharacterRepository,
        registry: ProviderRegistry,
        affect: AffectService,
    ) -> None:
        self.conversations = conversations
        self.messages = messages
        self.characters = characters
        self.registry = registry
        self.affect = affect

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
        return user_msg, reply_msg
