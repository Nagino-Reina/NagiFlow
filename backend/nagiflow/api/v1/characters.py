"""Character management endpoints."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import PaginationParams, get_current_active_user
from nagiflow.core.database import get_session
from nagiflow.models.user import User
from nagiflow.schemas.character import CharacterBrief, CharacterCreate, CharacterResponse, CharacterUpdate
from nagiflow.schemas.common import MessageResponse
from nagiflow.schemas.skill import AssignSkillRequest, CharacterSkillResponse
from nagiflow.services.character import CharacterService

router = APIRouter(prefix="/characters", tags=["Characters"])


@router.post("", response_model=CharacterResponse, status_code=201)
async def create_character(
    data: CharacterCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> CharacterResponse:
    """Create a new AI Vtuber character profile."""
    svc = CharacterService(db)
    character = await svc.create(current_user.id, data)
    return CharacterResponse.model_validate(character)


@router.get("", response_model=list[CharacterBrief])
async def list_characters(
    include_public: bool = Query(default=False),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[CharacterBrief]:
    """List characters owned by the current user, optionally including public ones."""
    svc = CharacterService(db)
    characters = await svc.list_for_user(
        current_user.id,
        include_public=include_public,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [CharacterBrief.model_validate(c) for c in characters]


@router.get("/{character_id}", response_model=CharacterResponse)
async def get_character(
    character_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> CharacterResponse:
    """Retrieve a character by ID."""
    svc = CharacterService(db)
    character = await svc.get(character_id, current_user.id)
    return CharacterResponse.model_validate(character)


@router.patch("/{character_id}", response_model=CharacterResponse)
async def update_character(
    character_id: UUID,
    data: CharacterUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> CharacterResponse:
    """Update a character's profile or settings."""
    svc = CharacterService(db)
    character = await svc.update(character_id, current_user.id, data)
    return CharacterResponse.model_validate(character)


@router.delete("/{character_id}", response_model=MessageResponse)
async def delete_character(
    character_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Delete a character and all associated workspace files."""
    svc = CharacterService(db)
    await svc.delete(character_id, current_user.id)
    return MessageResponse(message="Character deleted.")


# ---------------------------------------------------------------------------
# Asset upload endpoints
# ---------------------------------------------------------------------------


@router.post("/{character_id}/avatar", response_model=MessageResponse)
async def upload_avatar(
    character_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Upload an avatar image for a character."""
    svc = CharacterService(db)
    data = await file.read()
    path = await svc.save_avatar(character_id, current_user.id, data, file.filename or "avatar")
    return MessageResponse(message=f"Avatar saved to '{path}'.")


@router.post("/{character_id}/voice-sample", response_model=MessageResponse)
async def upload_voice_sample(
    character_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Upload a reference voice sample for TTS speaker matching."""
    svc = CharacterService(db)
    data = await file.read()
    path = await svc.save_voice_sample(character_id, current_user.id, data, file.filename or "voice_sample")
    return MessageResponse(message=f"Voice sample saved to '{path}'.")


@router.post("/{character_id}/model", response_model=MessageResponse)
async def upload_model(
    character_id: UUID,
    model_type: Literal["live2d", "3d"] = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """
    Upload a Live2D (.model3.json, .moc3, .zip) or 3D (.vrm, .glb, .gltf) model file.
    """
    svc = CharacterService(db)
    data = await file.read()
    path = await svc.save_model_file(
        character_id, current_user.id, data, file.filename or "model", model_type
    )
    return MessageResponse(message=f"Model saved to '{path}'.")


# ---------------------------------------------------------------------------
# Skill management
# ---------------------------------------------------------------------------


@router.get("/{character_id}/skills", response_model=list[CharacterSkillResponse])
async def list_character_skills(
    character_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[CharacterSkillResponse]:
    """List skills assigned to a character."""
    svc = CharacterService(db)
    char_skills = await svc.get_skills(character_id, current_user.id)
    return [
        CharacterSkillResponse(
            id=cs.id,
            character_id=cs.character_id,
            skill_id=cs.skill_id,
            skill_name=cs.skill.name,
            skill_display_name=cs.skill.display_name,
            config=cs.config,
            is_enabled=cs.is_enabled,
        )
        for cs in char_skills
    ]


@router.post("/{character_id}/skills", response_model=MessageResponse, status_code=201)
async def assign_skill(
    character_id: UUID,
    req: AssignSkillRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Assign a skill to a character."""
    svc = CharacterService(db)
    await svc.assign_skill(character_id, current_user.id, req)
    return MessageResponse(message="Skill assigned.")


@router.delete("/{character_id}/skills/{skill_id}", response_model=MessageResponse)
async def remove_skill(
    character_id: UUID,
    skill_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Remove a skill assignment from a character."""
    svc = CharacterService(db)
    await svc.remove_skill(character_id, current_user.id, skill_id)
    return MessageResponse(message="Skill removed.")
