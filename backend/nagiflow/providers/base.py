"""Provider interfaces + capability flags (docs/03 §6, docs/06 §5.1).

Every external capability is a typed Protocol with **capability flags** so the orchestrator
and UI adapt to what a provider supports. P0 fully defines the LLM contract; the others are
declared as seams (docs reserve them as extension space) and filled in later phases.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


class ProviderError(RuntimeError):
    """A provider failed at runtime — missing optional dependency, model load, or backend
    error. The service layer maps it to the `provider.*` error envelope (docs/05 §3)."""


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


# --- TTS (docs/06 §5.1, docs/08 §4) ---


@dataclass(frozen=True)
class TTSCaps:
    streaming: bool = False
    voice_clone: bool = False
    voice_design: bool = False
    fine_tune: bool = False
    sample_rate: int = 48000


@dataclass
class VoiceRef:
    """A resolved voice descriptor passed to a TTS provider for a single synthesis.

    `kind` is one of zero_shot | voice_design | fine_tuned (docs/08 §4). `reference_paths`
    are absolute paths the service resolved from the voice model's storage keys, so the
    provider never needs to know the workspace layout.
    """

    kind: str = "voice_design"
    reference_paths: list[str] = field(default_factory=list)
    design_description: str | None = None
    artifact_path: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class TTSProvider(Protocol):
    name: str
    capabilities: TTSCaps

    async def synthesize(
        self,
        *,
        text: str,
        voice: VoiceRef,
        style: str | None = None,
        speech_rate: float = 1.0,
    ) -> bytes:
        """Render `text` to a complete WAV byte payload."""
        ...

    async def health(self) -> bool: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str

    async def embed(self, texts: list[str]) -> list[list[float]]: ...

    async def health(self) -> bool: ...
