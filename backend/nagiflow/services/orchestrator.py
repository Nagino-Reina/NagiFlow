"""Dialogue orchestrator — minimal P1 slice (docs/03 §4, docs/11 §4).

Turns an inbound message into a character reply: resolve context → assemble prompt
(persona + Big Five directives + current emotion directive + recent history) → LLM generate.
The emotion directive is computed by the AffectService and passed in (docs/10 §7.1). Memory
retrieval/write, TTS, visemes, tools, and streaming are seams filled in later phases (P3/P5).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core import errors
from ..models.character import Character
from ..models.conversation import Message
from ..providers.base import ChatMessage, GenRequest, GenUsage, ProviderError
from ..providers.registry import ProviderRegistry
from . import personality

_HISTORY_LIMIT = 20


@dataclass
class TurnResult:
    text: str
    usage: GenUsage | None
    provider: str
    model: str | None


class DialogueOrchestrator:
    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    async def handle_turn(
        self,
        *,
        character: Character,
        history: list[Message],
        user_text: str,
        roleplay_prompt: str = "",
        affect_directive: str | None = None,
    ) -> TurnResult:
        system = personality.build_system_prompt(
            roleplay_prompt, character.persona, character.big_five
        )
        if affect_directive:
            system = f"{system}\n\n{affect_directive}"
        temperature = personality.temperature_for(character.big_five)

        messages: list[ChatMessage] = [ChatMessage(role="system", content=system)]
        for msg in history[-_HISTORY_LIMIT:]:
            if msg.role in ("user", "character"):
                messages.append(ChatMessage(role=msg.role, content=msg.content))
        messages.append(ChatMessage(role="user", content=user_text))

        llm = self.registry.get_llm()
        req = GenRequest(messages=messages, temperature=temperature, stream=True)

        parts: list[str] = []
        usage: GenUsage | None = None
        try:
            async for chunk in llm.generate(req):
                if chunk.delta:
                    parts.append(chunk.delta)
                if chunk.usage is not None:
                    usage = chunk.usage
        except ProviderError as exc:
            # Surface a clean provider.* envelope instead of a raw 500 (docs/03 §6,
            # docs/05 §3) — e.g. Ollama unreachable or the configured model is missing.
            raise errors.provider_error(llm.name, str(exc)) from exc
        return TurnResult(
            text="".join(parts).strip(),
            usage=usage,
            provider=llm.name,
            model=getattr(llm, "model", None),
        )
