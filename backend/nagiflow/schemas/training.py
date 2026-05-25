"""Pydantic schemas for TrainingDataset / TrainingItem."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# TrainingItem
# ---------------------------------------------------------------------------


class TrainingItemBase(BaseModel):
    text: str
    speaker_id: int | None = None
    source: str = "generated"
    quality_rating: int | None = Field(None, ge=1, le=5)


class TrainingItemCreate(TrainingItemBase):
    pass


class TrainingItemUpdate(BaseModel):
    text: str | None = None
    quality_rating: int | None = Field(None, ge=1, le=5)


class TrainingItemRead(TrainingItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dataset_id: uuid.UUID
    audio_path: str | None = None
    duration_ms: int | None = None


# ---------------------------------------------------------------------------
# TrainingDataset
# ---------------------------------------------------------------------------


class TrainingDatasetBase(BaseModel):
    name: str
    description: str | None = None
    character_id: uuid.UUID | None = None


class TrainingDatasetCreate(TrainingDatasetBase):
    pass


class TrainingDatasetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    character_id: uuid.UUID | None = None


class TrainingDatasetRead(TrainingDatasetBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    item_count: int = 0
    total_duration_ms: int = 0


class TrainingDatasetReadDetail(TrainingDatasetRead):
    items: list[TrainingItemRead] = []
