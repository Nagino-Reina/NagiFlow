"""Usage-record repository: writes + aggregation queries (docs/12 §3.1)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ..models.usage import UsageRecord


class UsageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.s = session

    def add(self, record: UsageRecord) -> UsageRecord:
        self.s.add(record)
        return record

    async def flush(self) -> None:
        await self.s.flush()

    def _scope(
        self,
        stmt,
        user_id: str,
        *,
        character_id: str | None = None,
        conversation_id: str | None = None,
        since: datetime | None = None,
    ):
        stmt = stmt.where(UsageRecord.user_id == user_id)
        if character_id:
            stmt = stmt.where(UsageRecord.character_id == character_id)
        if conversation_id:
            stmt = stmt.where(UsageRecord.conversation_id == conversation_id)
        if since:
            stmt = stmt.where(UsageRecord.occurred_at >= since)
        return stmt

    async def totals(self, user_id: str, **filters) -> dict:
        stmt = self._scope(
            select(
                func.count(UsageRecord.id),
                func.coalesce(func.sum(UsageRecord.prompt_tokens), 0),
                func.coalesce(func.sum(UsageRecord.completion_tokens), 0),
                func.coalesce(func.sum(UsageRecord.total_tokens), 0),
                func.coalesce(func.sum(UsageRecord.audio_seconds), 0.0),
                func.coalesce(func.sum(UsageRecord.est_cost), 0.0),
            ),
            user_id,
            **filters,
        )
        row = (await self.s.execute(stmt)).one()
        return {
            "calls": int(row[0]),
            "prompt_tokens": int(row[1]),
            "completion_tokens": int(row[2]),
            "total_tokens": int(row[3]),
            "audio_seconds": round(float(row[4]), 3),
            "est_cost": round(float(row[5]), 6),
        }

    async def grouped(
        self, key: ColumnElement, user_id: str, *, order_by_key: bool = False
    ) -> list[dict]:
        total = func.coalesce(func.sum(UsageRecord.total_tokens), 0)
        stmt = self._scope(
            select(key.label("key"), func.count(UsageRecord.id), total), user_id
        ).group_by(key)
        stmt = stmt.order_by(key.asc()) if order_by_key else stmt.order_by(total.desc())
        rows = (await self.s.execute(stmt)).all()
        return [
            {"key": r[0], "calls": int(r[1]), "total_tokens": int(r[2])} for r in rows
        ]

    async def recent(self, user_id: str, *, limit: int = 100, **filters) -> list[UsageRecord]:
        stmt = self._scope(select(UsageRecord), user_id, **filters)
        stmt = stmt.order_by(UsageRecord.occurred_at.desc()).limit(limit)
        return list((await self.s.execute(stmt)).scalars().all())
