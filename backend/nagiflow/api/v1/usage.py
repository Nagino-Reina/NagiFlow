"""Usage accounting endpoints (docs/05 §4.7, docs/12 §3, FR-OBS-3).

Token/audio usage scoped to the requesting user (single-user P1). `/usage` lists recent
records with filters + totals; `/usage:summary` returns the dashboard aggregates.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter

from ...schemas.observability import (
    UsageRecordOut,
    UsageResponse,
    UsageSummary,
    UsageTotals,
)
from ..deps import RequireUser, Usage

router = APIRouter(tags=["usage"])


@router.get("/usage", response_model=UsageResponse)
async def list_usage(
    principal: RequireUser,
    svc: Usage,
    character_id: str | None = None,
    conversation_id: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> UsageResponse:
    result = await svc.query(
        principal.user_id,
        character_id=character_id,
        conversation_id=conversation_id,
        since=since,
        limit=limit,
    )
    return UsageResponse(
        totals=UsageTotals(**result["totals"]),
        records=[UsageRecordOut.model_validate(r) for r in result["records"]],
    )


@router.get("/usage:summary", response_model=UsageSummary)
async def usage_summary(principal: RequireUser, svc: Usage) -> UsageSummary:
    data = await svc.summary(principal.user_id)
    return UsageSummary.model_validate(data)