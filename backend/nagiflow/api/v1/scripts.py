"""Script / Screenplay CRUD and TTS synthesis endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import get_current_active_user
from nagiflow.core.database import get_session
from nagiflow.models.user import User
from nagiflow.schemas.script import (
    ScriptCreate,
    ScriptLineCreate,
    ScriptLineRead,
    ScriptLineUpdate,
    ScriptRead,
    ScriptReadDetail,
    ScriptSceneCreate,
    ScriptSceneRead,
    ScriptSceneUpdate,
    ScriptUpdate,
)
from nagiflow.services.script import ScriptService

router = APIRouter(prefix="/scripts", tags=["Scripts"])


# ---------------------------------------------------------------------------
# Scripts
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ScriptRead])
async def list_scripts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[ScriptRead]:
    svc = ScriptService(db)
    scripts = await svc.list_for_user(current_user.id)
    return [ScriptRead.model_validate(s) for s in scripts]


@router.post("", response_model=ScriptRead, status_code=201)
async def create_script(
    data: ScriptCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ScriptRead:
    svc = ScriptService(db)
    script = await svc.create(current_user.id, data)
    await db.commit()
    return ScriptRead.model_validate(script)


@router.get("/{script_id}", response_model=ScriptReadDetail)
async def get_script(
    script_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ScriptReadDetail:
    svc = ScriptService(db)
    script = await svc.get(script_id, current_user.id, detail=True)
    return ScriptReadDetail.model_validate(script)


@router.patch("/{script_id}", response_model=ScriptRead)
async def update_script(
    script_id: UUID,
    data: ScriptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ScriptRead:
    svc = ScriptService(db)
    script = await svc.update(script_id, current_user.id, data)
    await db.commit()
    return ScriptRead.model_validate(script)


@router.delete("/{script_id}", status_code=204)
async def delete_script(
    script_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    svc = ScriptService(db)
    await svc.delete(script_id, current_user.id)
    await db.commit()


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------


@router.post("/{script_id}/scenes", response_model=ScriptSceneRead, status_code=201)
async def create_scene(
    script_id: UUID,
    data: ScriptSceneCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ScriptSceneRead:
    svc = ScriptService(db)
    scene = await svc.create_scene(script_id, current_user.id, data)
    await db.commit()
    return ScriptSceneRead.model_validate(scene)


@router.patch("/{script_id}/scenes/{scene_id}", response_model=ScriptSceneRead)
async def update_scene(
    script_id: UUID,
    scene_id: UUID,
    data: ScriptSceneUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ScriptSceneRead:
    svc = ScriptService(db)
    scene = await svc.update_scene(script_id, scene_id, current_user.id, data)
    await db.commit()
    return ScriptSceneRead.model_validate(scene)


@router.delete("/{script_id}/scenes/{scene_id}", status_code=204)
async def delete_scene(
    script_id: UUID,
    scene_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    svc = ScriptService(db)
    await svc.delete_scene(script_id, scene_id, current_user.id)
    await db.commit()


# ---------------------------------------------------------------------------
# Lines
# ---------------------------------------------------------------------------


@router.post(
    "/{script_id}/scenes/{scene_id}/lines",
    response_model=ScriptLineRead,
    status_code=201,
)
async def create_line(
    script_id: UUID,
    scene_id: UUID,
    data: ScriptLineCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ScriptLineRead:
    svc = ScriptService(db)
    line = await svc.create_line(script_id, scene_id, current_user.id, data)
    await db.commit()
    return ScriptLineRead.model_validate(line)


@router.patch(
    "/{script_id}/scenes/{scene_id}/lines/{line_id}",
    response_model=ScriptLineRead,
)
async def update_line(
    script_id: UUID,
    scene_id: UUID,
    line_id: UUID,
    data: ScriptLineUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ScriptLineRead:
    svc = ScriptService(db)
    line = await svc.update_line(script_id, scene_id, line_id, current_user.id, data)
    await db.commit()
    return ScriptLineRead.model_validate(line)


@router.delete(
    "/{script_id}/scenes/{scene_id}/lines/{line_id}",
    status_code=204,
)
async def delete_line(
    script_id: UUID,
    scene_id: UUID,
    line_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> None:
    svc = ScriptService(db)
    await svc.delete_line(script_id, scene_id, line_id, current_user.id)
    await db.commit()


# ---------------------------------------------------------------------------
# TTS Synthesis
# ---------------------------------------------------------------------------


@router.post(
    "/{script_id}/scenes/{scene_id}/lines/{line_id}/synthesize",
    response_model=ScriptLineRead,
)
async def synthesize_line(
    script_id: UUID,
    scene_id: UUID,
    line_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> ScriptLineRead:
    svc = ScriptService(db)
    line = await svc.synthesize_line(script_id, scene_id, line_id, current_user.id)
    await db.commit()
    return ScriptLineRead.model_validate(line)


@router.post("/{script_id}/synthesize_all")
async def synthesize_all(
    script_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> dict:
    svc = ScriptService(db)
    count = await svc.synthesize_all(script_id, current_user.id)
    await db.commit()
    return {"synthesized": count}


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


@router.get("/{script_id}/export")
async def export_script(
    script_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> Response:
    svc = ScriptService(db)
    zip_bytes = await svc.export_zip(script_id, current_user.id)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=script_{script_id}.zip"},
    )
