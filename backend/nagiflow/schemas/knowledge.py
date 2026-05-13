"""Knowledge base Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from nagiflow.schemas.common import OrmBase, TimestampSchema


class KnowledgeDocCreate(OrmBase):
    title: str = Field(min_length=1, max_length=512)
    description: str | None = None
    content: str | None = None  # direct text input
    source: str | None = None
    character_id: UUID | None = None  # None = global knowledge


class KnowledgeDocResponse(TimestampSchema):
    id: UUID
    user_id: UUID
    character_id: UUID | None
    title: str
    description: str | None
    source: str | None
    file_path: str | None
    chunk_count: int = 0


class KnowledgeSearchRequest(OrmBase):
    query: str
    top_k: int = Field(default=5, ge=1, le=50)
    character_id: UUID | None = None  # None = search all user's docs


class KnowledgeSearchResult(OrmBase):
    chunk_id: UUID
    document_id: UUID
    document_title: str
    content: str
    score: float
