"""User Pydantic schemas."""

import re
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from nagiflow.schemas.common import OrmBase, TimestampSchema

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")


class UserCreate(OrmBase):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not _USERNAME_RE.match(v):
            raise ValueError(
                "Username must be 3-64 characters and contain only letters, "
                "numbers, underscores, or hyphens."
            )
        return v.lower()


class UserUpdate(OrmBase):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=64)


class UserPasswordChange(OrmBase):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class UserResponse(TimestampSchema):
    id: UUID
    email: str
    username: str
    role: str
    is_active: bool


class TokenResponse(OrmBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(OrmBase):
    email: EmailStr
    password: str


class RefreshRequest(OrmBase):
    refresh_token: str
