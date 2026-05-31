"""Voice-model repository (docs/08 §4)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.character import VoiceModel


class VoiceModelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, voice_model_id: str) -> VoiceModel | None:
        return await self.s.get(VoiceModel, voice_model_id)

    async def list_for_character(self, character_id: str) -> list[VoiceModel]:
        stmt = (
            select(VoiceModel)
            .where(VoiceModel.character_id == character_id)
            .order_by(VoiceModel.created_at)
        )
        res = await self.s.execute(stmt)
        return list(res.scalars().all())

    def add(self, voice_model: VoiceModel) -> VoiceModel:
        self.s.add(voice_model)
        return voice_model

    async def delete(self, voice_model: VoiceModel) -> None:
        await self.s.delete(voice_model)

    async def flush(self) -> None:
        await self.s.flush()
