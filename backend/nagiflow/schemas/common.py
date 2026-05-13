"""Common Pydantic schema types and mixins."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrmBase(BaseModel):
    """Base schema that enables ORM mode for all response models."""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(OrmBase):
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(OrmBase):
    """Generic paginated list wrapper."""

    total: int
    page: int
    page_size: int
    items: list  # type: ignore[type-arg]


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class UUIDResponse(BaseModel):
    id: UUID
