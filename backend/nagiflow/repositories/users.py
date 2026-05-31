"""User & Session repositories."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import Session, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, user_id: str) -> User | None:
        return await self.s.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        res = await self.s.execute(select(User).where(User.username == username))
        return res.scalar_one_or_none()

    def add(self, user: User) -> User:
        self.s.add(user)
        return user


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get_by_token_hash(self, token_hash: str) -> Session | None:
        res = await self.s.execute(select(Session).where(Session.token_hash == token_hash))
        return res.scalar_one_or_none()

    def add(self, session_row: Session) -> Session:
        self.s.add(session_row)
        return session_row

    async def delete_by_id(self, session_id: str) -> None:
        await self.s.execute(delete(Session).where(Session.id == session_id))

    async def delete_for_user(self, user_id: str) -> None:
        await self.s.execute(delete(Session).where(Session.user_id == user_id))

    async def touch(self, session_row: Session, when: datetime) -> None:
        session_row.last_seen_at = when
