"""Voice schemas (docs/05 §4.1, docs/08 §4)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VoiceModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    character_id: str
    kind: str
    provider: str
    version: int
    design_description: str | None
    status: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class VoiceDesignCreate(BaseModel):
    design_description: str = Field(min_length=1, max_length=500)


class VoicePreviewRequest(BaseModel):
    text: str | None = Field(default=None, max_length=500)
    voice_model_id: str | None = None
    style: str | None = None
    speech_rate: float = Field(default=1.0, ge=0.5, le=2.0)


class TTSCapsOut(BaseModel):
    name: str
    streaming: bool
    voice_clone: bool
    voice_design: bool
    fine_tune: bool
    sample_rate: int
