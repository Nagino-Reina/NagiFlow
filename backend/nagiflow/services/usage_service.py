"""Usage accounting service (docs/12 §3, FR-OBS-3).

Records one row per model/provider call and serves totals + per-character / per-provider /
per-day breakdowns, all scoped to the requesting user (single-user P1; an operator view
across users lands with multi-user in P3).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func

from ..core.ids import new_id
from ..models.usage import UsageRecord
from ..repositories.usage import UsageRepository


class UsageService:
    def __init__(self, usage: UsageRepository) -> None:
        self.usage = usage

    async def record(
        self,
        *,
        kind: str,
        provider: str,
        model: str | None = None,
        user_id: str | None = None,
        character_id: str | None = None,
        conversation_id: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        audio_seconds: float | None = None,
        est_cost: float | None = None,
        correlation_id: str | None = None,
    ) -> UsageRecord:
        total = None
        if prompt_tokens is not None or completion_tokens is not None:
            total = (prompt_tokens or 0) + (completion_tokens or 0)
        record = UsageRecord(
            id=new_id("ur"),
            kind=kind,
            provider=provider,
            model=model,
            user_id=user_id,
            character_id=character_id,
            conversation_id=conversation_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            audio_seconds=audio_seconds,
            est_cost=est_cost,
            correlation_id=correlation_id,
        )
        self.usage.add(record)
        await self.usage.flush()
        return record

    async def query(
        self,
        user_id: str,
        *,
        character_id: str | None = None,
        conversation_id: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> dict:
        filters = {
            "character_id": character_id,
            "conversation_id": conversation_id,
            "since": since,
        }
        totals = await self.usage.totals(user_id, **filters)
        records = await self.usage.recent(user_id, limit=limit, **filters)
        return {"totals": totals, "records": records}

    async def summary(self, user_id: str) -> dict:
        return {
            "totals": await self.usage.totals(user_id),
            "by_character": await self.usage.grouped(UsageRecord.character_id, user_id),
            "by_provider": await self.usage.grouped(UsageRecord.provider, user_id),
            "by_day": await self.usage.grouped(
                func.date(UsageRecord.occurred_at), user_id, order_by_key=True
            ),
        }
