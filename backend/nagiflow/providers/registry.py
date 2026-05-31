"""Provider registry + configuration-driven selection (docs/03 §6).

Holds the active provider per capability and a fallback. P0 wires the LLM capability
(Ollama default, echo fallback); module-supplied providers register here later (docs/06).
"""

from __future__ import annotations

from ..config import Settings
from ..core.logging import get_logger
from .base import LLMProvider
from .llm.echo import EchoLLM
from .llm.ollama import OllamaLLM

log = get_logger("nagiflow.providers")


class ProviderRegistry:
    def __init__(self) -> None:
        self._llm: dict[str, LLMProvider] = {}
        self._default_llm: str = "echo"
        self._echo = EchoLLM()

    def register_llm(self, provider: LLMProvider, *, default: bool = False) -> None:
        self._llm[provider.name] = provider
        if default:
            self._default_llm = provider.name

    def get_llm(self, name: str | None = None) -> LLMProvider:
        key = name or self._default_llm
        return self._llm.get(key, self._echo)

    @property
    def echo_llm(self) -> LLMProvider:
        return self._echo


def build_registry(settings: Settings) -> ProviderRegistry:
    reg = ProviderRegistry()
    reg.register_llm(EchoLLM())
    if settings.default_llm == "ollama":
        reg.register_llm(
            OllamaLLM(settings.ollama_base_url, settings.ollama_model), default=True
        )
    else:
        reg.register_llm(EchoLLM(), default=True)
        log.info("LLM default set to offline echo provider")
    return reg
