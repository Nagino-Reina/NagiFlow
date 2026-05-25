"""OpenAI-compatible LLM plugin."""

from nagiflow.plugin.base import BasePlugin, PluginMeta
from nagiflow.plugin.registry import registry


class LLMOpenAICompatPlugin(BasePlugin):
    meta = PluginMeta(
        name="llm_openai_compat",
        version="1.0.0",
        description="OpenAI-compatible LLM provider (OpenAI, Azure, LM Studio, vLLM, etc.).",
    )

    async def setup(self) -> None:
        from .provider import OpenAICompatProvider

        registry.register_llm("openai_compat", OpenAICompatProvider)
