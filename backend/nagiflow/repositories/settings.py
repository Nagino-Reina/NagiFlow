"""App-settings repository — key/value runtime overrides (docs/05 §4.7)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.setting import AppSetting


class SettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    async def get(self, key: str) -> str | None:
        row = await self.s.get(AppSetting, key)
        return row.value if row else None

    async def set(self, key: str, value: str) -> None:
        row = await self.s.get(AppSetting, key)
        if row is None:
            self.s.add(AppSetting(key=key, value=value))
        else:
            row.value = value
        await self.s.flush()

    async def delete(self, key: str) -> None:
        row = await self.s.get(AppSetting, key)
        if row is not None:
            await self.s.delete(row)
            await self.s.flush()
