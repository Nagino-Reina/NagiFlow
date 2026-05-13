"""User management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import get_current_active_user, require_minimum_role
from nagiflow.core.database import get_session
from nagiflow.core.exceptions import NotFoundError, PermissionDeniedError
from nagiflow.core.security import UserRole, hash_password, verify_password
from nagiflow.models.user import User
from nagiflow.schemas.common import MessageResponse
from nagiflow.schemas.user import UserPasswordChange, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Update the current user's profile (email or username)."""
    if data.email:
        # Check uniqueness
        result = await db.execute(select(User).where(User.email == data.email))
        if result.scalar_one_or_none():
            from nagiflow.core.exceptions import ConflictError
            raise ConflictError("Email already in use.")
        current_user.email = data.email
    if data.username:
        result = await db.execute(select(User).where(User.username == data.username))
        if result.scalar_one_or_none():
            from nagiflow.core.exceptions import ConflictError
            raise ConflictError("Username already in use.")
        current_user.username = data.username
    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.post("/me/password", response_model=MessageResponse)
async def change_password(
    data: UserPasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Change the current user's password."""
    if not verify_password(data.current_password, current_user.hashed_password):
        raise PermissionDeniedError("Current password is incorrect.")
    current_user.hashed_password = hash_password(data.new_password)
    await db.flush()
    return MessageResponse(message="Password updated successfully.")


# ---------------------------------------------------------------------------
# Admin-only endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[UserResponse],
    dependencies=[Depends(require_minimum_role(UserRole.ADMIN))],
)
async def list_users(
    db: AsyncSession = Depends(get_session),
) -> list[User]:
    """List all users. Admin only."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


@router.patch(
    "/{user_id}/deactivate",
    response_model=MessageResponse,
    dependencies=[Depends(require_minimum_role(UserRole.ADMIN))],
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_admin: User = Depends(require_minimum_role(UserRole.ADMIN)),
) -> MessageResponse:
    """Deactivate a user account. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(f"User '{user_id}' not found.")
    if user.id == current_admin.id:
        raise PermissionDeniedError("Cannot deactivate your own account.")
    user.is_active = False
    await db.flush()
    return MessageResponse(message=f"User '{user.username}' deactivated.")


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
    dependencies=[Depends(require_minimum_role(UserRole.ADMIN))],
)
async def set_user_role(
    user_id: UUID,
    role: UserRole,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Set a user's role. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError(f"User '{user_id}' not found.")
    user.role = role.value
    await db.flush()
    await db.refresh(user)
    return user
