"""
Abstract base classes for LLM providers.

Third-party or user-contributed providers must implement ``BaseLLMProvider``
and register themselves via the plugin system.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMMessage:
    """A single message in an LLM conversation."""

    role: str  # "user" | "assistant" | "system"
    content: str


@dataclass
class LLMConfig:
    """Runtime configuration for a single LLM invocation."""

    model: str
    system_prompt: str = ""
    temperature: float = 0.8
    max_tokens: int = 2048
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"


class BaseLLMProvider(ABC):
    """
    Abstract interface for LLM providers.

    Implementors supply both a one-shot ``generate`` method and a streaming
    variant ``stream``.  All methods are async to support concurrent requests.
    """

    # Unique short name used to identify the provider in config / DB
    provider_name: str = "base"

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> LLMResponse:
        """Return a complete response in one call."""

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        config: LLMConfig,
    ) -> AsyncGenerator[str, None]:
        """
        Yield text delta chunks as the model generates them.

        Implementors must use ``yield`` so the return type is truly a generator.
        """
        # Stub to satisfy the type checker; concrete implementations must override.
        raise NotImplementedError
        yield  # pragma: no cover

    async def health_check(self) -> bool:
        """Return True if the provider endpoint is reachable."""
        return True
