"""
Abstract base class for TTS (Text-to-Speech) providers.

TTS providers convert text into audio bytes (PCM WAV by default).
Streaming providers yield audio chunks as they become available,
enabling low-latency playback on the client side.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any


@dataclass
class TTSConfig:
    """Runtime configuration for a TTS synthesis request."""

    speaker_id: int = 1
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    output_format: str = "wav"  # "wav" | "mp3" | "ogg"
    extra: dict[str, Any] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.extra is None:
            self.extra = {}


@dataclass
class TTSResult:
    audio_bytes: bytes
    sample_rate: int = 24000
    channels: int = 1
    format: str = "wav"


class BaseTTSProvider(ABC):
    """Abstract interface for TTS providers."""

    provider_name: str = "base"

    @abstractmethod
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult:
        """Convert *text* to audio and return the full result."""

    async def stream_synthesize(
        self, text: str, config: TTSConfig
    ) -> AsyncGenerator[bytes, None]:
        """
        Yield audio byte chunks as they are generated.

        The default implementation calls ``synthesize`` and yields the full
        result as a single chunk.  Providers that support native streaming
        should override this method.
        """
        result = await self.synthesize(text, config)
        yield result.audio_bytes

    @staticmethod
    def split_into_sentences(text: str) -> list[str]:
        """
        Heuristically split *text* into sentence-sized chunks for incremental
        TTS synthesis while the LLM is still generating.
        """
        import re

        parts = re.split(r"(?<=[.!?。！？])\s+", text.strip())
        return [p.strip() for p in parts if p.strip()]

    async def health_check(self) -> bool:
        return True
