"""Observability schemas — usage accounting + system resources (docs/05 §4.7, docs/12)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UsageTotals(BaseModel):
    calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    audio_seconds: float
    est_cost: float


class UsageGroup(BaseModel):
    key: str | None
    calls: int
    total_tokens: int


class UsageRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    provider: str
    model: str | None
    character_id: str | None
    conversation_id: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    audio_seconds: float | None
    occurred_at: datetime


class UsageResponse(BaseModel):
    totals: UsageTotals
    records: list[UsageRecordOut]


class UsageSummary(BaseModel):
    totals: UsageTotals
    by_character: list[UsageGroup]
    by_provider: list[UsageGroup]
    by_day: list[UsageGroup]


class MemoryStat(BaseModel):
    used: int
    total: int
    percent: float


class DiskStat(BaseModel):
    used: int
    total: int
    free: int
    percent: float


class GpuStat(BaseModel):
    name: str
    utilization_percent: float
    memory_used: int
    memory_total: int


class ProcessStat(BaseModel):
    pid: int
    rss: int


class SystemResources(BaseModel):
    cpu_percent: float
    cpu_count: int | None
    memory: MemoryStat
    disk: DiskStat
    process: ProcessStat
    gpus: list[GpuStat]
