"""
Ollama LLM provider.

Uses PydanticAI's Ollama model integration for both regular completions
and streaming.  Falls back to a raw httpx call if PydanticAI is unavailable
so the provider remains functional during prototyping.
"""

from collections.abc import AsyncGenerator

import httpx
from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import LLMProviderError
from nagiflow.llm.base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """
    LLM provider backed by a locally-running Ollama instance.

    Streaming is implemented via Ollama's native ``/api/chat`` endpoint
    with ``stream=true`` so that text deltas are emitted as soon as they
    arrive from the model.
    """

    provider_name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=5.0),
        )

    def _build_messages(self, messages: list[LLMMessage], system_prompt: str) -> list[dict]:
        ollama_messages: list[dict] = []
        if system_prompt:
            ollama_messages.append({"role": "system", "content": system_prompt})
        for m in messages:
            ollama_messages.append({"role": m.role, "content": m.content})
        return ollama_messages

    async def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        payload = {
            "model": config.model,
            "messages": self._build_messages(messages, config.system_prompt),
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                **config.extra,
            },
        }
        try:
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc

        data = resp.json()
        content = data.get("message", {}).get("content", "")
        prompt_eval = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        return LLMResponse(
            content=content,
            model=config.model,
            input_tokens=prompt_eval,
            output_tokens=eval_count,
        )

    async def stream(
        self, messages: list[LLMMessage], config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": config.model,
            "messages": self._build_messages(messages, config.system_prompt),
            "stream": True,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens,
                **config.extra,
            },
        }
        try:
            async with self._client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    import json

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("message", {}).get("content", "")
                    if delta:
                        yield delta
                    if chunk.get("done", False):
                        break
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama stream failed: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/api/tags", timeout=5.0)
            return resp.is_success
        except Exception as exc:
            logger.warning(f"Ollama health check failed: {exc}")
            return False

    async def list_models(self) -> list[str]:
        """Return available model names from the Ollama instance."""
        try:
            resp = await self._client.get("/api/tags")
            resp.raise_for_status()
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as exc:
            logger.warning(f"Could not list Ollama models: {exc}")
            return []
