"""
Knowledge base service.

Handles document ingestion with chunking, embedding storage, and
semantic retrieval (RAG).  Supports both text input and file uploads.
"""

from __future__ import annotations

import textwrap
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nagiflow.core.exceptions import NotFoundError, PermissionDeniedError
from nagiflow.models.knowledge import KnowledgeChunk, KnowledgeDocument
from nagiflow.schemas.knowledge import KnowledgeDocCreate, KnowledgeSearchResult
from nagiflow.services.embedding import EmbeddingService, embedding_service

# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

DEFAULT_CHUNK_SIZE = 512     # characters
DEFAULT_CHUNK_OVERLAP = 64   # characters


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """
    Split *text* into overlapping chunks of at most *chunk_size* characters.

    A simple character-level sliding window that tries to break at sentence
    boundaries first.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        if end >= len(text):
            chunks.append(text[start:])
            break
        # Try to find a sentence boundary within the last 20% of the window
        boundary = text.rfind(". ", start + chunk_size // 5 * 4, end)
        if boundary == -1:
            boundary = end
        else:
            boundary += 1  # include the period

        chunks.append(text[start:boundary].strip())
        start = boundary - overlap

    return [c for c in chunks if c]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class KnowledgeService:
    def __init__(self, db: AsyncSession, embedder: EmbeddingService | None = None) -> None:
        self.db = db
        self.embedder = embedder or embedding_service

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def create(
        self,
        user_id: UUID,
        data: KnowledgeDocCreate,
        file_path: str | None = None,
    ) -> KnowledgeDocument:
        doc = KnowledgeDocument(
            user_id=user_id,
            character_id=data.character_id,
            title=data.title,
            description=data.description,
            source=data.source,
            file_path=file_path,
        )
        self.db.add(doc)
        await self.db.flush()

        # Ingest content
        content = data.content or ""
        if content:
            await self._ingest_text(doc.id, content)

        await self.db.refresh(doc)
        logger.info(f"Created knowledge document '{doc.title}' ({doc.id}) for user {user_id}")
        return doc

    async def ingest_file_content(self, doc_id: UUID, text: str) -> int:
        """
        Chunk and embed *text*, attaching all chunks to the document.
        Returns the number of chunks created.
        """
        return await self._ingest_text(doc_id, text)

    async def _ingest_text(self, doc_id: UUID, text: str) -> int:
        chunks = chunk_text(text)
        for idx, chunk_text_item in enumerate(chunks):
            embedding = await self.embedder.embed(chunk_text_item)
            chunk = KnowledgeChunk(
                document_id=doc_id,
                content=chunk_text_item,
                chunk_index=idx,
                embedding=embedding,
            )
            self.db.add(chunk)
        await self.db.flush()
        logger.debug(f"Ingested {len(chunks)} chunks for document {doc_id}")
        return len(chunks)

    async def get(self, doc_id: UUID, user_id: UUID) -> KnowledgeDocument:
        result = await self.db.execute(
            select(KnowledgeDocument)
            .options(selectinload(KnowledgeDocument.chunks))
            .where(KnowledgeDocument.id == doc_id)
        )
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError(f"Knowledge document '{doc_id}' not found.")
        if doc.user_id != user_id:
            raise PermissionDeniedError()
        return doc

    async def list_for_user(
        self,
        user_id: UUID,
        character_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeDocument]:
        stmt = select(KnowledgeDocument).where(KnowledgeDocument.user_id == user_id)
        if character_id is not None:
            stmt = stmt.where(KnowledgeDocument.character_id == character_id)
        stmt = stmt.order_by(KnowledgeDocument.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, doc_id: UUID, user_id: UUID) -> None:
        doc = await self.get(doc_id, user_id)
        await self.db.delete(doc)
        logger.info(f"Deleted knowledge document {doc_id}")

    # ------------------------------------------------------------------
    # Semantic search (RAG)
    # ------------------------------------------------------------------

    async def search(
        self,
        user_id: UUID,
        query: str,
        top_k: int = 5,
        character_id: UUID | None = None,
    ) -> list[KnowledgeSearchResult]:
        """
        Retrieve the top-k most relevant knowledge chunks for *query*.

        If *character_id* is provided, only chunks from documents scoped
        to that character (or global documents for the user) are searched.
        """
        query_emb = await self.embedder.embed(query)

        # Load all relevant chunks with their parent document
        stmt = (
            select(KnowledgeChunk)
            .join(KnowledgeDocument)
            .where(KnowledgeDocument.user_id == user_id)
        )
        if character_id is not None:
            from sqlalchemy import or_
            stmt = stmt.where(
                or_(
                    KnowledgeDocument.character_id == character_id,
                    KnowledgeDocument.character_id.is_(None),
                )
            )
        result = await self.db.execute(stmt.options(selectinload(KnowledgeChunk.document)))
        chunks = list(result.scalars().all())

        if not chunks:
            return []

        candidates = [(str(c.id), c.embedding or []) for c in chunks]
        id_to_chunk = {str(c.id): c for c in chunks}

        scored = self.embedder.top_k_by_similarity(query_emb, candidates, k=top_k)

        return [
            KnowledgeSearchResult(
                chunk_id=UUID(cid),
                document_id=id_to_chunk[cid].document_id,
                document_title=id_to_chunk[cid].document.title,
                content=id_to_chunk[cid].content,
                score=score,
            )
            for cid, score in scored
            if cid in id_to_chunk
        ]

    async def format_context(
        self,
        user_id: UUID,
        query: str,
        top_k: int = 3,
        character_id: UUID | None = None,
    ) -> str:
        """Return a formatted string for LLM context injection."""
        results = await self.search(user_id, query, top_k=top_k, character_id=character_id)
        if not results:
            return ""
        parts = [f"[{r.document_title}]\n{r.content}" for r in results]
        return "\n\n".join(parts)
