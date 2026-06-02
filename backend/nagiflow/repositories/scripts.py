"""Script + ScriptLine repositories (docs/04 §5.3-5.4)."""

from __future__ import annotations

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.script import Script, ScriptLine


class ScriptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    def add(self, script: Script) -> Script:
        self.s.add(script)
        return script

    async def flush(self) -> None:
        await self.s.flush()

    async def get(self, script_id: str) -> Script | None:
        return await self.s.get(Script, script_id)

    async def list(self) -> list[Script]:
        rows = await self.s.execute(
            select(Script).where(Script.status != "archived").order_by(Script.updated_at.desc())
        )
        return list(rows.scalars().all())

    async def line_count(self, script_id: str) -> int:
        rows = await self.s.execute(
            select(func.count(ScriptLine.id)).where(ScriptLine.script_id == script_id)
        )
        return rows.scalar_one()

    async def delete(self, script: Script) -> None:
        await self.s.execute(delete(ScriptLine).where(ScriptLine.script_id == script.id))
        await self.s.delete(script)


class ScriptLineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    def add(self, line: ScriptLine) -> ScriptLine:
        self.s.add(line)
        return line

    async def flush(self) -> None:
        await self.s.flush()

    async def get(self, line_id: str) -> ScriptLine | None:
        return await self.s.get(ScriptLine, line_id)

    async def list_for_script(self, script_id: str) -> list[ScriptLine]:
        rows = await self.s.execute(
            select(ScriptLine)
            .where(ScriptLine.script_id == script_id)
            .order_by(ScriptLine.order_index)
        )
        return list(rows.scalars().all())

    async def next_order_index(self, script_id: str) -> int:
        rows = await self.s.execute(
            select(func.max(ScriptLine.order_index)).where(ScriptLine.script_id == script_id)
        )
        current = rows.scalar()
        return 0 if current is None else current + 1

    async def delete(self, line: ScriptLine) -> None:
        await self.s.delete(line)
