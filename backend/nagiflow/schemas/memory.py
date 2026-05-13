"""Long-term memory Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from nagiflow.schemas.common import OrmBase, TimestampSchema


class MemoryCreate(OrmBase):
    content: str = Field(min_length=1)
    importance: float = Field(default=5.0, ge=0.0, le=10.0)
    source: str | None = None


class MemoryUpdate(OrmBase):
    content: str | None = None
    importance: float | None = Field(default=None, ge=0.0, le=10.0)


class MemoryResponse(TimestampSchema):
    id: UUID
    character_id: UUID
    user_id: UUID
    content: str
    importance: float
    access_count: int
    source: str | None


class MemorySearchRequest(OrmBase):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    min_importance: float = Field(default=0.0, ge=0.0, le=10.0)
