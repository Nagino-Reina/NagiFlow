"""
Long-term memory service.

Manages per-character, per-user memory entries with:
  - CRUD operations
  - Semantic similarity search via embeddings
  - Automatic importance-weighted retrieval ranking
  - Memory consolidation (summarisation of older entries)
"""

from __future__ import annotations

from uuid import UUID

from loguru import logger
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.core.exceptions import NotFoundError, PermissionDeniedError
from nagiflow.models.memory import LongTermMemory
from nagiflow.schemas.memory import MemoryCreate, MemoryUpdate
from nagiflow.services.embedding import EmbeddingService, embedding_service


class MemoryService:
    def __init__(self, db: AsyncSession, embedder: EmbeddingService | None = None) -> None:
        self.db = db
        self.embedder = embedder or embedding_service

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create(
        self, character_id: UUID, user_id: UUID, data: MemoryCreate
    ) -> LongTermMemory:
        embedding = await self.embedder.embed(data.content)
        memory = LongTermMemory(
            character_id=character_id,
            user_id=user_id,
            content=data.content,
            embedding=embedding,
            importance=data.importance,
            source=data.source,
        )
        self.db.add(memory)
        await self.db.flush()
        await self.db.refresh(memory)
        logger.debug(f"Created memory {memory.id} for character {character_id}")
        return memory

    async def get(self, memory_id: UUID, user_id: UUID) -> LongTermMemory:
        result = await self.db.execute(
            select(LongTermMemory).where(LongTermMemory.id == memory_id)
        )
        memory = result.scalar_one_or_none()
        if memory is None:
            raise NotFoundError(f"Memory '{memory_id}' not found.")
        if memory.user_id != user_id:
            raise PermissionDeniedError()
        return memory

    async def list_for_character(
        self, character_id: UUID, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[LongTermMemory]:
        result = await self.db.execute(
            select(LongTermMemory)
            .where(
                LongTermMemory.character_id == character_id,
                LongTermMemory.user_id == user_id,
            )
            .order_by(LongTermMemory.importance.desc(), LongTermMemory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(
        self, memory_id: UUID, user_id: UUID, data: MemoryUpdate
    ) -> LongTermMemory:
        memory = await self.get(memory_id, user_id)
        if data.content is not None:
            memory.content = data.content
            memory.embedding = await self.embedder.embed(data.content)
        if data.importance is not None:
            memory.importance = data.importance
        await self.db.flush()
        await self.db.refresh(memory)
        return memory

    async def delete(self, memory_id: UUID, user_id: UUID) -> None:
        memory = await self.get(memory_id, user_id)
        await self.db.delete(memory)

    async def delete_all_for_character(self, character_id: UUID, user_id: UUID) -> int:
        result = await self.db.execute(
            delete(LongTermMemory)
            .where(
                LongTermMemory.character_id == character_id,
                LongTermMemory.user_id == user_id,
            )
            .returning(LongTermMemory.id)
        )
        deleted = len(result.fetchall())
        logger.info(f"Deleted {deleted} memories for character {character_id}")
        return deleted

    # ------------------------------------------------------------------
    # Semantic search
    # ------------------------------------------------------------------

    async def search(
        self,
        character_id: UUID,
        user_id: UUID,
        query: str,
        top_k: int = 5,
        min_importance: float = 0.0,
    ) -> list[tuple[LongTermMemory, float]]:
        """Return the top-k most semantically relevant memories with scores."""
        query_emb = await self.embedder.embed(query)

        result = await self.db.execute(
            select(LongTermMemory).where(
                LongTermMemory.character_id == character_id,
                LongTermMemory.user_id == user_id,
                LongTermMemory.importance >= min_importance,
            )
        )
        memories = list(result.scalars().all())
        if not memories:
            return []

        candidates = [
            (str(m.id), m.embedding or [])
            for m in memories
        ]
        id_to_memory = {str(m.id): m for m in memories}

        scored = self.embedder.top_k_by_similarity(query_emb, candidates, k=top_k)

        # Increment access count for retrieved memories
        retrieved_ids = [UUID(mid) for mid, _ in scored]
        await self.db.execute(
            update(LongTermMemory)
            .where(LongTermMemory.id.in_(retrieved_ids))
            .values(access_count=LongTermMemory.access_count + 1)
        )

        return [(id_to_memory[mid], score) for mid, score in scored if mid in id_to_memory]

    async def format_context(
        self,
        character_id: UUID,
        user_id: UUID,
        query: str,
        top_k: int = 5,
    ) -> str:
        """
        Return a formatted string of relevant memories suitable for
        injection into an LLM system prompt.
        """
        results = await self.search(character_id, user_id, query, top_k=top_k)
        if not results:
            return ""
        lines = [f"- {m.content}" for m, _ in results]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Auto-ingest from conversation turn
    # ------------------------------------------------------------------

    async def ingest_from_message(
        self,
        character_id: UUID,
        user_id: UUID,
        text: str,
        importance: float = 3.0,
    ) -> LongTermMemory | None:
        """
        Attempt to extract and store a memorable fact from a message.

        Currently uses a simple heuristic (message length threshold).
        Replace with an LLM-based extraction pipeline for production.
        """
        if len(text) < 40:
            return None
        data = MemoryCreate(content=text[:1000], importance=importance, source="conversation")
        return await self.create(character_id, user_id, data)
