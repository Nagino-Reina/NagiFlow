"""
Embedding service for semantic search.

Generates vector embeddings for text using the configured provider
(Ollama embedding model, OpenAI, or a simple fallback).

The default provider uses Ollama's ``/api/embeddings`` endpoint with the
``nomic-embed-text`` model.  The ``simple`` fallback hashes the text into a
fixed-dimension pseudo-embedding for development/testing.
"""

from __future__ import annotations

import hashlib
import math
from typing import Literal

import httpx
import numpy as np
from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import EmbeddingProviderError


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Return cosine similarity between two equal-length vectors."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(va)
    norm_b = np.linalg.norm(vb)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(va, vb) / (norm_a * norm_b))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Public helper for similarity comparisons."""
    return _cosine_similarity(a, b)


def _simple_embed(text: str, dim: int = 128) -> list[float]:
    """
    Deterministic pseudo-embedding via SHA-256.

    Not semantically meaningful—use only as a fallback when no real
    embedding model is available.
    """
    digest = hashlib.sha256(text.encode()).digest()
    nums = [b / 255.0 for b in digest]
    # Tile to reach the required dimension
    tiled = (nums * math.ceil(dim / len(nums)))[:dim]
    # Normalise
    norm = math.sqrt(sum(x * x for x in tiled)) or 1.0
    return [x / norm for x in tiled]


class EmbeddingService:
    """Service for generating text embeddings."""

    def __init__(
        self,
        provider: Literal["ollama_embed", "openai_embed", "simple"] | None = None,
        model: str | None = None,
        dimension: int | None = None,
    ) -> None:
        self.provider = provider or settings.EMBEDDING_PROVIDER
        self.model = model or settings.EMBEDDING_MODEL
        self.dimension = dimension or settings.EMBEDDING_DIMENSION
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def embed(self, text: str) -> list[float]:
        """Return a normalised embedding vector for *text*."""
        text = text.strip()
        if not text:
            return [0.0] * self.dimension

        if self.provider == "simple":
            return _simple_embed(text, self.dimension)
        if self.provider == "ollama_embed":
            return await self._ollama_embed(text)
        if self.provider == "openai_embed":
            return await self._openai_embed(text)

        raise EmbeddingProviderError(f"Unknown embedding provider: {self.provider}")

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts (sequential for providers that lack batch endpoints)."""
        return [await self.embed(t) for t in texts]

    async def _ollama_embed(self, text: str) -> list[float]:
        client = self._get_client()
        try:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            resp.raise_for_status()
            return resp.json()["embedding"]
        except Exception as exc:
            logger.warning(f"Ollama embedding failed, falling back to simple: {exc}")
            return _simple_embed(text, self.dimension)

    async def _openai_embed(self, text: str) -> list[float]:
        client = self._get_client()
        try:
            resp = await client.post(
                f"{settings.OPENAI_BASE_URL}/embeddings",
                json={"model": self.model, "input": text},
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]
        except Exception as exc:
            raise EmbeddingProviderError(f"OpenAI embedding failed: {exc}") from exc

    def top_k_by_similarity(
        self,
        query_embedding: list[float],
        candidates: list[tuple[str, list[float]]],
        k: int = 5,
        min_score: float = 0.0,
    ) -> list[tuple[str, float]]:
        """
        Return the top-k candidates sorted by cosine similarity.

        Args:
            query_embedding: Embedding of the search query.
            candidates: List of (id_or_text, embedding) tuples.
            k: Maximum number of results to return.
            min_score: Minimum similarity threshold.

        Returns:
            Sorted list of (id_or_text, score) tuples, highest score first.
        """
        scored = [
            (label, _cosine_similarity(query_embedding, emb))
            for label, emb in candidates
            if emb
        ]
        filtered = [(lbl, s) for lbl, s in scored if s >= min_score]
        filtered.sort(key=lambda x: x[1], reverse=True)
        return filtered[:k]


# Module-level singleton
embedding_service = EmbeddingService()
