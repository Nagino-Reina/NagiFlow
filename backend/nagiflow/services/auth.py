"""
Authentication service.

Handles user registration, login (credential verification + token issuance),
token refresh, and the bootstrap of the first admin account.
"""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from nagiflow.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from nagiflow.models.user import User
from nagiflow.schemas.user import TokenResponse, UserCreate


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register(self, data: UserCreate) -> User:
        # Check for duplicate email
        if await self._get_by_email(data.email):
            raise ConflictError(f"Email '{data.email}' is already registered.")
        # Check for duplicate username
        if await self._get_by_username(data.username):
            raise ConflictError(f"Username '{data.username}' is already taken.")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            role="user",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        logger.info(f"Registered new user: {user.email} ({user.id})")
        return user

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationError("Account is inactive.")
        return self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_refresh_token(refresh_token)
        user_id = UUID(payload["sub"])
        user = await self.get_user(user_id)
        if not user.is_active:
            raise AuthenticationError("Account is inactive.")
        return self._issue_tokens(user)

    async def get_user(self, user_id: UUID) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError(f"User '{user_id}' not found.")
        return user

    async def get_user_by_email(self, email: str) -> User:
        user = await self._get_by_email(email)
        if user is None:
            raise NotFoundError(f"User with email '{email}' not found.")
        return user

    async def _get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    def _issue_tokens(user: User) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user.id, user.role),
            refresh_token=create_refresh_token(user.id),
        )

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    async def ensure_admin(self, email: str, password: str) -> User | None:
        """
        Create the initial admin account if no users exist yet.
        Called once during application startup.
        """
        if not email or not password:
            return None

        result = await self.db.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return None  # users already exist

        user = User(
            email=email,
            username="admin",
            hashed_password=hash_password(password),
            role="admin",
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        logger.info(f"Admin account bootstrapped: {user.email}")
        return user
