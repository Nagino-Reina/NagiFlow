"""Media-asset repository (docs/04 §5.6)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.media import MediaAsset


class MediaAssetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, media_id: str) -> MediaAsset | None:
        return await self.s.get(MediaAsset, media_id)

    def add(self, asset: MediaAsset) -> MediaAsset:
        self.s.add(asset)
        return asset

    async def flush(self) -> None:
        await self.s.flush()
