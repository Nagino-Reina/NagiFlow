"""Ollama LLM plugin."""

from nagiflow.plugin.base import BasePlugin, PluginMeta
from nagiflow.plugin.registry import registry


class LLMOllamaPlugin(BasePlugin):
    meta = PluginMeta(
        name="llm_ollama",
        version="1.0.0",
        description="Ollama local LLM provider.",
    )

    async def setup(self) -> None:
        from .provider import OllamaProvider

        registry.register_llm("ollama", OllamaProvider)
