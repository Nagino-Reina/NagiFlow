"""
Security utilities: password hashing, JWT creation/verification, and
role-based access-control helpers.
"""

from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

from jose import JWTError, jwt
from pwdlib import PasswordHash

from nagiflow.config import settings
from nagiflow.core.exceptions import AuthenticationError, PermissionDeniedError, TokenExpiredError

# ---------------------------------------------------------------------------
# Password
# ---------------------------------------------------------------------------

_pwd_hasher = PasswordHash.recommended()

def hash_password(plain: str) -> str:
    return _pwd_hasher.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_hasher.verify(plain, hashed)


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------


class UserRole(StrEnum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.USER: 0,
    UserRole.MODERATOR: 1,
    UserRole.ADMIN: 2,
}


def require_role(user_role: str, minimum: UserRole) -> None:
    """Raise PermissionDeniedError if *user_role* is below *minimum*."""
    current_level = ROLE_HIERARCHY.get(UserRole(user_role), -1)
    required_level = ROLE_HIERARCHY[minimum]
    if current_level < required_level:
        raise PermissionDeniedError(
            f"This action requires at least the '{minimum}' role."
        )


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

_TOKEN_TYPE_ACCESS = "access"
_TOKEN_TYPE_REFRESH = "refresh"


def _create_token(
    subject: str | UUID,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(tz=timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "typ": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: UUID, role: str) -> str:
    return _create_token(
        subject=user_id,
        token_type=_TOKEN_TYPE_ACCESS,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"role": role},
    )


def create_refresh_token(user_id: UUID) -> str:
    return _create_token(
        subject=user_id,
        token_type=_TOKEN_TYPE_REFRESH,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str = _TOKEN_TYPE_ACCESS) -> dict[str, Any]:
    """Decode and validate a JWT. Raises appropriate NagiFlowErrors."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        if "expired" in str(exc).lower():
            raise TokenExpiredError() from exc
        raise AuthenticationError() from exc

    if payload.get("typ") != expected_type:
        raise AuthenticationError("Invalid token type.")

    return payload


def decode_access_token(token: str) -> dict[str, Any]:
    return decode_token(token, _TOKEN_TYPE_ACCESS)


def decode_refresh_token(token: str) -> dict[str, Any]:
    return decode_token(token, _TOKEN_TYPE_REFRESH)
