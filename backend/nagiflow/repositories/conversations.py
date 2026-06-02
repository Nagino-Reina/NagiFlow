"""Conversation & message repositories."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.conversation import Conversation, ConversationParticipant, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, conversation_id: str) -> Conversation | None:
        return await self.s.get(Conversation, conversation_id)

    async def list_for_user(self, user_id: str, *, limit: int = 50) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        res = await self.s.execute(stmt)
        return list(res.scalars().all())

    def add(self, conversation: Conversation) -> Conversation:
        self.s.add(conversation)
        return conversation

    async def delete(self, conversation: Conversation) -> None:
        cid = conversation.id
        await self.s.execute(delete(Message).where(Message.conversation_id == cid))
        await self.s.execute(
            delete(ConversationParticipant).where(ConversationParticipant.conversation_id == cid)
        )
        await self.s.delete(conversation)


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, message_id: str) -> Message | None:
        return await self.s.get(Message, message_id)

    async def list_for_conversation(
        self, conversation_id: str, *, limit: int = 100
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(limit)
        )
        res = await self.s.execute(stmt)
        return list(res.scalars().all())

    def add(self, message: Message) -> Message:
        self.s.add(message)
        return message
