"""Authentication endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import get_current_active_user
from nagiflow.core.database import get_session
from nagiflow.models.user import User
from nagiflow.schemas.user import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserResponse
from nagiflow.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_session),
) -> User:
    """Register a new user account."""
    svc = AuthService(db)
    return await svc.register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Authenticate with email and password, receive JWT tokens."""
    svc = AuthService(db)
    return await svc.login(data.email, data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Exchange a refresh token for a new access/refresh token pair."""
    svc = AuthService(db)
    return await svc.refresh(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Return the currently authenticated user's profile."""
    return current_user
