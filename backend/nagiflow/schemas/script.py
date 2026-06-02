"""Script schemas (docs/05 §4.2, docs/07)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

ScriptStatus = Literal["draft", "review", "ready", "archived"]
SpeechRate = Annotated[float, Field(ge=0.5, le=2.0)]


class ScriptCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    language: str = "en"
    default_character_id: str | None = None


class ScriptUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    language: str | None = None
    status: ScriptStatus | None = None
    default_character_id: str | None = None


class ScriptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    language: str
    status: ScriptStatus
    source_kind: str
    default_character_id: str | None
    line_count: int = 0
    created_at: datetime
    updated_at: datetime


# --- lines ---


class ScriptLineCreate(BaseModel):
    text: str = ""
    character_id: str | None = None
    character_name_raw: str | None = None
    style: str | None = None
    speech_rate: SpeechRate | None = None
    reference_audio_key: str | None = None
    pause_after_ms: int | None = Field(default=None, ge=0)
    language: str | None = None
    notes: str | None = None
    start_ms: int | None = Field(default=None, ge=0)
    end_ms: int | None = Field(default=None, ge=0)


class ScriptLineUpdate(BaseModel):
    text: str | None = None
    character_id: str | None = None
    character_name_raw: str | None = None
    style: str | None = None
    speech_rate: SpeechRate | None = None
    reference_audio_key: str | None = None
    pause_after_ms: int | None = Field(default=None, ge=0)
    language: str | None = None
    notes: str | None = None
    start_ms: int | None = Field(default=None, ge=0)
    end_ms: int | None = Field(default=None, ge=0)
    take: int | None = Field(default=None, ge=1)


class ScriptLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    script_id: str
    order_index: int
    character_id: str | None
    character_name_raw: str | None
    text: str
    start_ms: int | None
    end_ms: int | None
    reference_audio_key: str | None
    style: str | None
    speech_rate: float | None
    pause_after_ms: int | None
    language: str | None
    notes: str | None
    take: int
    confidence: float | None


class ReorderIn(BaseModel):
    line_ids: list[str] = Field(min_length=1)


class ValidationIssue(BaseModel):
    severity: Literal["error", "warning"]
    code: str
    message: str
    line_id: str | None = None


class ValidationOut(BaseModel):
    issues: list[ValidationIssue]
