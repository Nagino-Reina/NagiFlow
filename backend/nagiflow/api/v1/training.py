"""TTS Training dataset endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import get_current_active_user
from nagiflow.core.database import get_session
from nagiflow.models.user import User
from nagiflow.schemas.training import (
    TrainingDatasetCreate,
    TrainingDatasetRead,
    TrainingDatasetReadDetail,
    TrainingDatasetUpdate,
    TrainingItemCreate,
    TrainingItemRead,
    TrainingItemUpdate,
)
from nagiflow.services.training import TrainingService

router = APIRouter(prefix="/training/datasets", tags=["Training"])


# ---------------------------------------------------------------------------
# Datasets
# ---------------------------------------------------------------------------


@router.get("", response_model=list[TrainingDatasetRead])
async def list_datasets(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[TrainingDatasetRead]:
    svc = TrainingService(db)
    datasets = await svc.list_datasets(current_user.id)
    return [TrainingDatasetRead.model_validate(d) for d in datasets]


@router.post("", response_model=TrainingDatasetRead, status_code=201)
async def create_dataset(
    data: TrainingDatasetCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> TrainingDatasetRead:
    svc = TrainingService(db)
    dataset = await svc.create_dataset(current_user.id, data)
    await db.commit()
    return TrainingDatasetRead.model_validate(dataset)


@router.get("/{dataset_id}", response_model=TrainingDatasetReadDetail)
async def get_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> TrainingDatasetReadDetail:
    svc = TrainingService(db)
    dataset = await svc.get_dataset(dataset_id, current_user.id, detail=True)
    return TrainingDatasetReadDetail.model_validate(dataset)


@router.patch("/{dataset_id}", response_model=TrainingDatasetRead)
async def update_dataset(
    dataset_id: UUID,
    data: TrainingDatasetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> TrainingDatasetRead:
    svc = TrainingService(db)
    dataset = await svc.update_dataset(dataset_id, current_user.id, data)
    await db.commit()
    return TrainingDatasetRead.model_validate(dataset)


@router.delete("/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    svc = TrainingService(db)
    await svc.delete_dataset(dataset_id, current_user.id)
    await db.commit()


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------


@router.post("/{dataset_id}/items", response_model=TrainingItemRead, status_code=201)
async def add_item(
    dataset_id: UUID,
    text: str = Form(...),
    speaker_id: int | None = Form(None),
    source: str = Form("imported"),
    audio: UploadFile | None = File(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> TrainingItemRead:
    svc = TrainingService(db)
    audio_bytes = await audio.read() if audio else None
    data = TrainingItemCreate(text=text, speaker_id=speaker_id, source=source)
    item = await svc.add_item(dataset_id, current_user.id, data, audio_bytes)
    await db.commit()
    return TrainingItemRead.model_validate(item)


@router.patch("/{dataset_id}/items/{item_id}", response_model=TrainingItemRead)
async def update_item(
    dataset_id: UUID,
    item_id: UUID,
    data: TrainingItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> TrainingItemRead:
    svc = TrainingService(db)
    item = await svc.update_item(dataset_id, item_id, current_user.id, data)
    await db.commit()
    return TrainingItemRead.model_validate(item)


@router.delete("/{dataset_id}/items/{item_id}", status_code=204)
async def delete_item(
    dataset_id: UUID,
    item_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    svc = TrainingService(db)
    await svc.delete_item(dataset_id, item_id, current_user.id)
    await db.commit()


@router.post("/{dataset_id}/items/generate", response_model=TrainingItemRead, status_code=201)
async def generate_item(
    dataset_id: UUID,
    text: str = Form(...),
    speaker_id: int | None = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> TrainingItemRead:
    """Generate TTS audio from text and add it as a new training item."""
    svc = TrainingService(db)
    item = await svc.generate_item(dataset_id, current_user.id, text, speaker_id)
    await db.commit()
    return TrainingItemRead.model_validate(item)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


@router.get("/{dataset_id}/export")
async def export_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> Response:
    svc = TrainingService(db)
    zip_bytes = await svc.export_zip(dataset_id, current_user.id)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=training_{dataset_id}.zip"
        },
    )
