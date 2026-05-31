"""Character repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.character import Character


class CharacterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, character_id: str) -> Character | None:
        return await self.s.get(Character, character_id)

    async def list(
        self, *, guest_visible_only: bool, limit: int = 50, cursor: str | None = None
    ) -> list[Character]:
        stmt = select(Character).where(Character.status != "archived")
        if guest_visible_only:
            stmt = stmt.where(Character.guest_visible.is_(True))
        if cursor:
            stmt = stmt.where(Character.id > cursor)
        stmt = stmt.order_by(Character.id).limit(limit)
        res = await self.s.execute(stmt)
        return list(res.scalars().all())

    def add(self, character: Character) -> Character:
        self.s.add(character)
        return character
