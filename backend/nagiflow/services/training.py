"""TTS Training dataset service."""

from __future__ import annotations

import io
import json
import uuid
import zipfile
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nagiflow.core.exceptions import NotFoundError, PermissionDeniedError
from nagiflow.core.workspace import workspace
from nagiflow.models.training import TrainingDataset, TrainingItem
from nagiflow.services._tts import resolve_tts
from nagiflow.schemas.training import (
    TrainingDatasetCreate,
    TrainingDatasetUpdate,
    TrainingItemCreate,
    TrainingItemUpdate,
)


class TrainingService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Dataset CRUD
    # ------------------------------------------------------------------

    async def create_dataset(
        self, user_id: UUID, data: TrainingDatasetCreate
    ) -> TrainingDataset:
        dataset = TrainingDataset(owner_id=user_id, **data.model_dump())
        self.db.add(dataset)
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset

    async def get_dataset(
        self, dataset_id: UUID, user_id: UUID, *, detail: bool = False
    ) -> TrainingDataset:
        stmt = select(TrainingDataset).where(TrainingDataset.id == dataset_id)
        if detail:
            stmt = stmt.options(selectinload(TrainingDataset.items))
        result = await self.db.execute(stmt)
        dataset = result.scalar_one_or_none()
        if dataset is None:
            raise NotFoundError(f"Training dataset '{dataset_id}' not found.")
        if dataset.owner_id != user_id:
            raise PermissionDeniedError()
        return dataset

    async def list_datasets(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[TrainingDataset]:
        result = await self.db.execute(
            select(TrainingDataset)
            .where(TrainingDataset.owner_id == user_id)
            .order_by(TrainingDataset.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_dataset(
        self, dataset_id: UUID, user_id: UUID, data: TrainingDatasetUpdate
    ) -> TrainingDataset:
        dataset = await self.get_dataset(dataset_id, user_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(dataset, k, v)
        await self.db.flush()
        await self.db.refresh(dataset)
        return dataset

    async def delete_dataset(self, dataset_id: UUID, user_id: UUID) -> None:
        dataset = await self.get_dataset(dataset_id, user_id)
        await self.db.delete(dataset)

    # ------------------------------------------------------------------
    # Item CRUD
    # ------------------------------------------------------------------

    async def add_item(
        self,
        dataset_id: UUID,
        user_id: UUID,
        data: TrainingItemCreate,
        audio_bytes: bytes | None = None,
    ) -> TrainingItem:
        dataset = await self.get_dataset(dataset_id, user_id)

        item = TrainingItem(dataset_id=dataset_id, **data.model_dump())
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)

        if audio_bytes:
            dest = (
                workspace.base
                / "training"
                / str(dataset_id)
                / f"{item.id}.wav"
            )
            await workspace.save_file(dest, audio_bytes)
            item.audio_path = str(workspace.relative_to_workspace(dest))

        # Update denormalized counters
        dataset.item_count += 1
        if item.duration_ms:
            dataset.total_duration_ms += item.duration_ms

        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def get_item(
        self, dataset_id: UUID, item_id: UUID, user_id: UUID
    ) -> TrainingItem:
        await self.get_dataset(dataset_id, user_id)
        result = await self.db.execute(
            select(TrainingItem).where(
                TrainingItem.id == item_id, TrainingItem.dataset_id == dataset_id
            )
        )
        item = result.scalar_one_or_none()
        if item is None:
            raise NotFoundError(f"Training item '{item_id}' not found.")
        return item

    async def update_item(
        self,
        dataset_id: UUID,
        item_id: UUID,
        user_id: UUID,
        data: TrainingItemUpdate,
    ) -> TrainingItem:
        item = await self.get_item(dataset_id, item_id, user_id)
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(item, k, v)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete_item(
        self, dataset_id: UUID, item_id: UUID, user_id: UUID
    ) -> None:
        dataset = await self.get_dataset(dataset_id, user_id)
        item = await self.get_item(dataset_id, item_id, user_id)

        dataset.item_count = max(0, dataset.item_count - 1)
        if item.duration_ms:
            dataset.total_duration_ms = max(
                0, dataset.total_duration_ms - item.duration_ms
            )

        await self.db.delete(item)

    # ------------------------------------------------------------------
    # TTS Generation
    # ------------------------------------------------------------------

    async def generate_item(
        self,
        dataset_id: UUID,
        user_id: UUID,
        text: str,
        speaker_id: int | None = None,
    ) -> TrainingItem:
        """Generate TTS audio for *text* and add as a new item."""
        dataset = await self.get_dataset(dataset_id, user_id)

        char = None
        if dataset.character_id:
            from nagiflow.models.character import Character
            result = await self.db.execute(
                select(Character).where(Character.id == dataset.character_id)
            )
            char = result.scalar_one_or_none()

        tts, tts_config = resolve_tts(char, speaker_id_override=speaker_id)
        tts_result = await tts.synthesize(text, tts_config)
        spk = tts_config.speaker_id

        create_data = TrainingItemCreate(
            text=text, speaker_id=spk, source="generated"
        )
        return await self.add_item(
            dataset_id, user_id, create_data, audio_bytes=tts_result.audio_bytes
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    async def export_zip(self, dataset_id: UUID, user_id: UUID) -> bytes:
        """Return a ZIP with all WAV files and a metadata.json."""
        dataset = await self.get_dataset(dataset_id, user_id, detail=True)

        metadata: list[dict] = []
        buf = io.BytesIO()

        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in dataset.items:
                entry: dict = {
                    "id": str(item.id),
                    "text": item.text,
                    "source": item.source,
                    "speaker_id": item.speaker_id,
                    "duration_ms": item.duration_ms,
                    "quality_rating": item.quality_rating,
                }
                if item.audio_path:
                    abs_path = workspace.abs_path(item.audio_path)
                    if abs_path.exists():
                        arcname = f"wavs/{item.id}.wav"
                        zf.write(abs_path, arcname)
                        entry["file"] = arcname
                metadata.append(entry)

            zf.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

        return buf.getvalue()
