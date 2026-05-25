"""
NagiFlow plugin base classes.

All provider interfaces and the BasePlugin contract live here.
Plugin authors import from this module to implement new providers or skills.
"""

from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

# Shared expression-tag utilities used by streaming and avatar providers.
_EXPRESSION_RE = re.compile(r"\[(\w+)\]")
_KNOWN_EXPRESSIONS = frozenset({"default", "happy", "sad", "angry", "surprised"})


def extract_expression(text: str) -> str:
    """Return the last recognised emotion tag in *text*, or ``'default'``."""
    for m in reversed(_EXPRESSION_RE.findall(text)):
        if m.lower() in _KNOWN_EXPRESSIONS:
            return m.lower()
    return "default"


def strip_expression_tags(text: str) -> str:
    """Remove all ``[emotion]`` tags from *text*."""
    return _EXPRESSION_RE.sub("", text).strip()


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------


@dataclass
class LLMMessage:
    role: str   # "user" | "assistant" | "system"
    content: str


@dataclass
class LLMConfig:
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
    provider_name: str = "base"

    @abstractmethod
    async def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse: ...

    @abstractmethod
    async def stream(
        self, messages: list[LLMMessage], config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        raise NotImplementedError
        yield  # pragma: no cover

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------


@dataclass
class TTSConfig:
    speaker_id: int = 1
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    output_format: str = "wav"
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class TTSResult:
    audio_bytes: bytes
    sample_rate: int = 24000
    channels: int = 1
    format: str = "wav"
    duration_ms: int = 0


class BaseTTSProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def synthesize(self, text: str, config: TTSConfig) -> TTSResult: ...

    async def stream_synthesize(
        self, text: str, config: TTSConfig
    ) -> AsyncGenerator[bytes, None]:
        result = await self.synthesize(text, config)
        yield result.audio_bytes

    @staticmethod
    def split_into_sentences(text: str) -> list[str]:
        parts = re.split(r"(?<=[.!?。！？])\s+", text.strip())
        return [p.strip() for p in parts if p.strip()]

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Avatar
# ---------------------------------------------------------------------------


@dataclass
class AvatarState:
    state: str = "idle"          # "idle" | "talking" | "blinking"
    expression: str = "default"  # "default" | "happy" | "sad" | "angry" | "surprised"


class BaseAvatarProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    def get_states(self) -> list[str]: ...

    @abstractmethod
    def get_expressions(self) -> list[str]: ...

    @abstractmethod
    def compute_state(self, audio_active: bool, expression: str = "default") -> AvatarState: ...

    def parse_expression_tag(self, text: str) -> tuple[str, str]:
        """
        Extract the last recognised [expression] tag from *text*.
        Returns ``(text_with_tags_stripped, expression_name)``.
        """
        expr = extract_expression(text)
        return strip_expression_tags(text), expr

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------


class BaseEmbeddingProvider(ABC):
    provider_name: str = "base"

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        import asyncio
        return list(await asyncio.gather(*[self.embed(t) for t in texts]))

    async def health_check(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@dataclass
class SkillParameter:
    name: str
    type: str          # "string" | "integer" | "number" | "boolean" | "array" | "object"
    description: str
    required: bool = True
    default: Any = None
    enum: list[Any] | None = None


@dataclass
class SkillMeta:
    name: str
    display_name: str
    description: str
    parameters: list[SkillParameter] = field(default_factory=list)
    is_builtin: bool = True

    def to_json_schema(self) -> dict:
        properties: dict[str, Any] = {}
        required: list[str] = []
        for p in self.parameters:
            prop: dict[str, Any] = {"type": p.type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            properties[p.name] = prop
            if p.required:
                required.append(p.name)
        return {"type": "object", "properties": properties, "required": required}

    def to_db_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "skill_type": "builtin" if self.is_builtin else "plugin",
            "entry_point": None,
            "default_config": {},
            "config_schema": self.to_json_schema(),
            "is_active": True,
            "is_builtin": self.is_builtin,
        }


class BaseSkill(ABC):
    meta: SkillMeta

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str: ...

    async def __call__(self, **kwargs: Any) -> str:
        return await self.execute(**kwargs)

    def as_tool_definition(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.meta.name,
                "description": self.meta.description,
                "parameters": self.meta.to_json_schema(),
            },
        }


# ---------------------------------------------------------------------------
# Plugin
# ---------------------------------------------------------------------------


@dataclass
class PluginMeta:
    name: str
    version: str = "0.1.0"
    author: str = ""
    description: str = ""
    requires: list[str] = field(default_factory=list)


class BasePlugin(ABC):
    meta: PluginMeta

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config: dict[str, Any] = config or {}

    @abstractmethod
    async def setup(self) -> None: ...

    async def teardown(self) -> None:
        pass
