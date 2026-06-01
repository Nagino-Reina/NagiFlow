"""Affect-state repository (docs/04 §5.9)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.affect import AffectState


class AffectStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get_for(
        self,
        character_id: str,
        user_id: str | None,
        counterpart_character_id: str | None = None,
    ) -> AffectState | None:
        stmt = select(AffectState).where(
            AffectState.character_id == character_id,
            AffectState.user_id == user_id,
            AffectState.counterpart_character_id == counterpart_character_id,
        )
        res = await self.s.execute(stmt)
        return res.scalars().first()

    def add(self, state: AffectState) -> AffectState:
        self.s.add(state)
        return state

    async def flush(self) -> None:
        await self.s.flush()
