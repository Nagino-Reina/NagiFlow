"""
Character-aware LLM agent.

This module wires together:
  - Character personality → system prompt
  - Long-term memory retrieval → context injection
  - Knowledge base retrieval → RAG context
  - Agent skills (tools) → dynamic tool binding
  - Streaming / one-shot generation

The agent is re-created per request so that character-specific configuration
(provider, model, skills) is always up-to-date.
"""

from __future__ import annotations

import textwrap
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from loguru import logger

from nagiflow.config import settings
from nagiflow.llm.base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse
from nagiflow.llm.providers.ollama import OllamaProvider
from nagiflow.llm.providers.openai_compat import OpenAICompatProvider

if TYPE_CHECKING:
    from nagiflow.models.character import Character
    from nagiflow.skills.base import BaseSkill

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_PROVIDER_MAP: dict[str, type[BaseLLMProvider]] = {
    "ollama": OllamaProvider,
    "openai_compat": OpenAICompatProvider,
}


def register_llm_provider(name: str, cls: type[BaseLLMProvider]) -> None:
    """Register a custom LLM provider (called from plugins)."""
    _PROVIDER_MAP[name] = cls
    logger.info(f"Registered LLM provider: '{name}'")


def get_llm_provider(name: str | None = None) -> BaseLLMProvider:
    """Instantiate the requested provider (or the configured default)."""
    provider_name = name or settings.DEFAULT_LLM_PROVIDER
    cls = _PROVIDER_MAP.get(provider_name)
    if cls is None:
        raise ValueError(
            f"Unknown LLM provider '{provider_name}'. "
            f"Available: {list(_PROVIDER_MAP)}"
        )
    return cls()


# ---------------------------------------------------------------------------
# System prompt builder
# ---------------------------------------------------------------------------


def build_system_prompt(character: "Character", memory_ctx: str = "", knowledge_ctx: str = "") -> str:
    """
    Construct a system prompt from the character's profile, Big Five personality,
    retrieved memories, and relevant knowledge snippets.
    """
    p = character.personality or {}
    big_five = p.get("big_five", {})
    custom = p.get("custom", {})

    def score(key: str) -> str:
        v = big_five.get(key, 50)
        return f"{v:.0f}/100"

    # Translate Big Five scores into descriptive trait phrases
    def openness_desc(v: float) -> str:
        return "highly creative and curious" if v >= 65 else "practical and conventional" if v <= 35 else "moderately open to new experiences"

    def conscientiousness_desc(v: float) -> str:
        return "very organised and dependable" if v >= 65 else "flexible and spontaneous" if v <= 35 else "moderately organised"

    def extraversion_desc(v: float) -> str:
        return "energetic, talkative, and enthusiastic" if v >= 65 else "quiet and reserved" if v <= 35 else "moderately outgoing"

    def agreeableness_desc(v: float) -> str:
        return "warm, cooperative, and empathetic" if v >= 65 else "direct and competitive" if v <= 35 else "balanced in cooperation"

    def neuroticism_desc(v: float) -> str:
        return "emotionally sensitive and reactive" if v >= 65 else "calm and emotionally stable" if v <= 35 else "moderately emotionally stable"

    o = float(big_five.get("openness", 50))
    c = float(big_five.get("conscientiousness", 50))
    e = float(big_five.get("extraversion", 50))
    a = float(big_five.get("agreeableness", 50))
    n = float(big_five.get("neuroticism", 50))

    personality_block = textwrap.dedent(f"""
        Personality traits (Big Five):
        - Openness ({score('openness')}): {openness_desc(o)}
        - Conscientiousness ({score('conscientiousness')}): {conscientiousness_desc(c)}
        - Extraversion ({score('extraversion')}): {extraversion_desc(e)}
        - Agreeableness ({score('agreeableness')}): {agreeableness_desc(a)}
        - Neuroticism ({score('neuroticism')}): {neuroticism_desc(n)}
    """).strip()

    custom_block = ""
    if custom:
        pairs = "\n".join(f"- {k}: {v}" for k, v in custom.items())
        custom_block = f"\nAdditional character details:\n{pairs}"

    memory_block = ""
    if memory_ctx:
        memory_block = f"\n\nRelevant memories about this user:\n{memory_ctx}"

    knowledge_block = ""
    if knowledge_ctx:
        knowledge_block = f"\n\nRelevant knowledge:\n{knowledge_ctx}"

    base_instructions = character.system_prompt or (
        "Respond naturally and stay fully in character at all times. "
        "Keep replies conversational and engaging."
    )

    return textwrap.dedent(f"""
        You are {character.name}.
        {character.description or ''}

        {personality_block}{custom_block}

        {base_instructions}{memory_block}{knowledge_block}
    """).strip()


# ---------------------------------------------------------------------------
# CharacterAgent
# ---------------------------------------------------------------------------


class CharacterAgent:
    """
    High-level wrapper around a character + LLM provider pair.

    Skills are injected as callable tool wrappers.  The agent is stateless
    between calls; all conversation context must be passed explicitly.
    """

    def __init__(
        self,
        character: "Character",
        provider: BaseLLMProvider | None = None,
        skills: list["BaseSkill"] | None = None,
    ) -> None:
        self.character = character
        self.provider = provider or get_llm_provider(character.llm_provider)
        self.skills = skills or []
        self._model = character.llm_model or settings.DEFAULT_LLM_MODEL

    def _make_config(self, **overrides: Any) -> LLMConfig:
        return LLMConfig(
            model=self._model,
            temperature=overrides.pop("temperature", 0.8),
            max_tokens=overrides.pop("max_tokens", 2048),
            extra=overrides,
        )

    async def _resolve_context(
        self,
        user_message: str,
        memory_context: str = "",
        knowledge_context: str = "",
    ) -> str:
        return build_system_prompt(self.character, memory_context, knowledge_context)

    async def generate(
        self,
        history: list[LLMMessage],
        user_message: str,
        memory_context: str = "",
        knowledge_context: str = "",
        **llm_kwargs: Any,
    ) -> LLMResponse:
        """One-shot generation with optional memory/knowledge injection."""
        system = await self._resolve_context(user_message, memory_context, knowledge_context)
        messages = [*history, LLMMessage(role="user", content=user_message)]
        config = self._make_config(**llm_kwargs)
        config.system_prompt = system
        return await self.provider.generate(messages, config)

    async def stream(
        self,
        history: list[LLMMessage],
        user_message: str,
        memory_context: str = "",
        knowledge_context: str = "",
        **llm_kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream text deltas with optional memory/knowledge injection."""
        system = await self._resolve_context(user_message, memory_context, knowledge_context)
        messages = [*history, LLMMessage(role="user", content=user_message)]
        config = self._make_config(**llm_kwargs)
        config.system_prompt = system
        async for chunk in self.provider.stream(messages, config):
            yield chunk
