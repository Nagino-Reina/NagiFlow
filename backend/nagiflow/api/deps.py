"""
FastAPI dependency providers.

These are injected via ``Depends()`` in route handlers.

Usage::

    @router.get("/me")
    async def me(user: User = Depends(get_current_user)):
        ...

    @router.delete("/characters/{character_id}")
    async def delete(
        character_id: UUID,
        user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_session),
    ):
        ...
"""

from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.core.database import get_session
from nagiflow.core.exceptions import AuthenticationError
from nagiflow.core.security import UserRole, decode_access_token, require_role
from nagiflow.models.user import User
from nagiflow.services.auth import AuthService

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Extract and validate the JWT bearer token, returning the current user."""
    if credentials is None:
        raise AuthenticationError("Missing Authorization header.")
    payload = decode_access_token(credentials.credentials)
    user_id = UUID(payload["sub"])
    auth_svc = AuthService(db)
    user = await auth_svc.get_user(user_id)
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    from nagiflow.core.exceptions import PermissionDeniedError

    if not current_user.is_active:
        raise PermissionDeniedError("Account is inactive.")
    return current_user


def require_minimum_role(role: UserRole):
    """Return a dependency that enforces a minimum role level."""

    async def _check(user: User = Depends(get_current_active_user)) -> User:
        require_role(user.role, role)
        return user

    return _check


# ---------------------------------------------------------------------------
# Common pagination query parameters
# ---------------------------------------------------------------------------


class PaginationParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
