"""Provider interfaces + capability flags (docs/03 §6, docs/06 §5.1).

Every external capability is a typed Protocol with **capability flags** so the orchestrator
and UI adapt to what a provider supports. P0 fully defines the LLM contract; the others are
declared as seams (docs reserve them as extension space) and filled in later phases.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


# --- LLM ---


@dataclass(frozen=True)
class LLMCaps:
    streaming: bool = True
    tools: bool = False
    embeddings: bool = False
    context_window: int = 8192


@dataclass
class ChatMessage:
    role: str  # system | user | assistant | tool
    content: str


@dataclass
class GenRequest:
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = True
    tools: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GenUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


@dataclass
class GenChunk:
    delta: str = ""
    done: bool = False
    usage: GenUsage | None = None


@runtime_checkable
class LLMProvider(Protocol):
    name: str
    capabilities: LLMCaps

    async def generate(self, req: GenRequest) -> AsyncIterator[GenChunk]: ...

    async def list_models(self) -> list[str]: ...

    async def health(self) -> bool: ...


# --- other capability seams (filled in later phases) ---


@dataclass(frozen=True)
class TTSCaps:
    streaming: bool = False
    voice_clone: bool = False
    voice_design: bool = False
    fine_tune: bool = False
    sample_rate: int = 48000


@runtime_checkable
class TTSProvider(Protocol):
    name: str
    capabilities: TTSCaps

    async def synthesize(self, *, text: str, voice: dict[str, Any]) -> bytes: ...

    async def health(self) -> bool: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str

    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    async def health(self) -> bool: ...
