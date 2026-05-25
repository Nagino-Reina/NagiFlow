"""
Character-aware LLM agent.

Wires together character personality, long-term memory, knowledge base RAG,
and agent skills into a single generate/stream interface.  Re-created per
request so character configuration is always fresh.
"""

from __future__ import annotations

import re
import textwrap
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

from loguru import logger

from nagiflow.config import settings
from nagiflow.plugin.base import LLMConfig, LLMMessage, LLMResponse
from nagiflow.plugin.registry import registry

if TYPE_CHECKING:
    from nagiflow.models.character import Character
    from nagiflow.plugin.base import BaseSkill


def build_system_prompt(
    character: "Character",
    memory_ctx: str = "",
    knowledge_ctx: str = "",
) -> str:
    p = character.personality or {}
    big_five = p.get("big_five", {})
    custom = p.get("custom", {})

    def score(k: str) -> str:
        return f"{big_five.get(k, 50):.0f}/100"

    def desc(val: float, high: str, mid: str, low: str) -> str:
        return high if val >= 65 else low if val <= 35 else mid

    o, c, e, a, n = (
        float(big_five.get("openness", 50)),
        float(big_five.get("conscientiousness", 50)),
        float(big_five.get("extraversion", 50)),
        float(big_five.get("agreeableness", 50)),
        float(big_five.get("neuroticism", 50)),
    )

    personality_block = textwrap.dedent(f"""
        Personality traits (Big Five):
        - Openness ({score('openness')}): {desc(o, 'highly creative and curious', 'moderately open', 'practical and conventional')}
        - Conscientiousness ({score('conscientiousness')}): {desc(c, 'very organised and dependable', 'moderately organised', 'flexible and spontaneous')}
        - Extraversion ({score('extraversion')}): {desc(e, 'energetic, talkative, and enthusiastic', 'moderately outgoing', 'quiet and reserved')}
        - Agreeableness ({score('agreeableness')}): {desc(a, 'warm, cooperative, and empathetic', 'balanced in cooperation', 'direct and competitive')}
        - Neuroticism ({score('neuroticism')}): {desc(n, 'emotionally sensitive and reactive', 'moderately stable', 'calm and emotionally stable')}
    """).strip()

    custom_block = ""
    if custom:
        custom_block = "\nAdditional character details:\n" + "\n".join(f"- {k}: {v}" for k, v in custom.items())

    memory_block = f"\n\nRelevant memories about this user:\n{memory_ctx}" if memory_ctx else ""
    knowledge_block = f"\n\nRelevant knowledge:\n{knowledge_ctx}" if knowledge_ctx else ""

    base = character.system_prompt or (
        "Respond naturally and stay fully in character at all times. "
        "Keep replies conversational and engaging."
    )

    return textwrap.dedent(f"""
        You are {character.name}.
        {character.description or ''}

        {personality_block}{custom_block}

        {base}{memory_block}{knowledge_block}
    """).strip()


# Regex to detect emotion tags like [happy], [sad], etc.
_EMOTION_RE = re.compile(r"\[(\w+)\]")


class CharacterAgent:
    """High-level wrapper around a Character + LLM provider."""

    def __init__(
        self,
        character: "Character",
        skills: list["BaseSkill"] | None = None,
    ) -> None:
        self.character = character
        self._provider = registry.get_llm(character.llm_provider)
        self.skills = skills or []
        self._model = character.llm_model or settings.DEFAULT_LLM_MODEL

    def _make_config(self, **overrides: Any) -> LLMConfig:
        return LLMConfig(
            model=self._model,
            temperature=overrides.pop("temperature", 0.8),
            max_tokens=overrides.pop("max_tokens", 2048),
            extra=overrides,
        )

    async def generate(
        self,
        history: list[LLMMessage],
        user_message: str,
        memory_context: str = "",
        knowledge_context: str = "",
        **llm_kwargs: Any,
    ) -> LLMResponse:
        system = build_system_prompt(self.character, memory_context, knowledge_context)
        messages = [*history, LLMMessage(role="user", content=user_message)]
        config = self._make_config(**llm_kwargs)
        config.system_prompt = system
        return await self._provider.generate(messages, config)

    async def stream(
        self,
        history: list[LLMMessage],
        user_message: str,
        memory_context: str = "",
        knowledge_context: str = "",
        **llm_kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        system = build_system_prompt(self.character, memory_context, knowledge_context)
        messages = [*history, LLMMessage(role="user", content=user_message)]
        config = self._make_config(**llm_kwargs)
        config.system_prompt = system
        async for chunk in self._provider.stream(messages, config):
            yield chunk
