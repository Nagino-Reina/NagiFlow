"""Long-term memory ORM model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from nagiflow.models.base import Base, TimestampMixin, new_uuid

if TYPE_CHECKING:
    from nagiflow.models.character import Character
    from nagiflow.models.user import User


class LongTermMemory(Base, TimestampMixin):
    """
    A semantically-indexed memory entry for a specific character.

    Memories persist across conversations and are retrieved via cosine
    similarity of their stored embedding vector.

    ``user_id`` tracks *whose* memory this is so that different users who
    share the same character can have separate memory spaces.
    """

    __tablename__ = "long_term_memories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    character_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Embedding stored as a JSON array of floats.
    # For production, replace with a dedicated vector column (pgvector, sqlite-vec).
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    # 0-10 importance score; influences retrieval ranking
    importance: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)

    # How many times this memory has been accessed (for decay / eviction)
    access_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Optional source tag: "conversation", "manual", "summarisation", etc.
    source: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    character: Mapped["Character"] = relationship("Character", back_populates="memories")
