"""Conversation & message repositories."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.conversation import Conversation, Message


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


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

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
