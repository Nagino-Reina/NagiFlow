"""Pydantic schemas for Script / ScriptScene / ScriptLine."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# ScriptLine
# ---------------------------------------------------------------------------


class ScriptLineBase(BaseModel):
    text: str = ""
    order: int = 0
    character_id: uuid.UUID | None = None
    notes: str | None = None


class ScriptLineCreate(ScriptLineBase):
    pass


class ScriptLineUpdate(BaseModel):
    text: str | None = None
    order: int | None = None
    character_id: uuid.UUID | None = None
    notes: str | None = None


class ScriptLineRead(ScriptLineBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scene_id: uuid.UUID
    audio_path: str | None = None
    duration_ms: int | None = None


# ---------------------------------------------------------------------------
# ScriptScene
# ---------------------------------------------------------------------------


class ScriptSceneBase(BaseModel):
    title: str = "Scene"
    order: int = 0


class ScriptSceneCreate(ScriptSceneBase):
    pass


class ScriptSceneUpdate(BaseModel):
    title: str | None = None
    order: int | None = None


class ScriptSceneRead(ScriptSceneBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    script_id: uuid.UUID
    lines: list[ScriptLineRead] = []


# ---------------------------------------------------------------------------
# Script
# ---------------------------------------------------------------------------


class ScriptBase(BaseModel):
    title: str
    description: str | None = None


class ScriptCreate(ScriptBase):
    pass


class ScriptUpdate(BaseModel):
    title: str | None = None
    description: str | None = None


class ScriptRead(ScriptBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID


class ScriptReadDetail(ScriptRead):
    scenes: list[ScriptSceneRead] = []
