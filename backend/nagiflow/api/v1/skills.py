"""Skills library endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import get_current_active_user, require_minimum_role
from nagiflow.core.database import get_session
from nagiflow.core.exceptions import NotFoundError
from nagiflow.core.security import UserRole
from nagiflow.models.skill import Skill
from nagiflow.models.user import User
from nagiflow.schemas.common import MessageResponse
from nagiflow.schemas.skill import SkillResponse

router = APIRouter(prefix="/skills", tags=["Skills Library"])


@router.get("", response_model=list[SkillResponse])
async def list_skills(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> list[SkillResponse]:
    """List all active skills available in the registry."""
    result = await db.execute(
        select(Skill)
        .where(Skill.is_active.is_(True))
        .order_by(Skill.is_builtin.desc(), Skill.display_name)
    )
    return [SkillResponse.model_validate(s) for s in result.scalars().all()]


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> SkillResponse:
    """Get a skill by ID."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise NotFoundError(f"Skill '{skill_id}' not found.")
    return SkillResponse.model_validate(skill)


@router.patch(
    "/{skill_id}/toggle",
    response_model=SkillResponse,
    dependencies=[Depends(require_minimum_role(UserRole.ADMIN))],
)
async def toggle_skill(
    skill_id: UUID,
    db: AsyncSession = Depends(get_session),
) -> SkillResponse:
    """Enable or disable a skill globally. Admin only."""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if skill is None:
        raise NotFoundError(f"Skill '{skill_id}' not found.")
    skill.is_active = not skill.is_active
    await db.flush()
    await db.refresh(skill)
    return SkillResponse.model_validate(skill)
