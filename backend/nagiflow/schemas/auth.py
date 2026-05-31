"""Auth schemas (docs/05 §2)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)
    display_name: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class SessionResponse(BaseModel):
    token: str
    user_id: str
    kind: str  # guest | user
    expires_at: datetime


class MeResponse(BaseModel):
    user_id: str
    kind: str  # guest | user
    is_admin: bool
    username: str | None = None
    display_name: str | None = None
