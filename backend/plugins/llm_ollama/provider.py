"""Ollama LLM provider implementation."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx
from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import LLMProviderError
from nagiflow.plugin.base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """LLM provider backed by a locally-running Ollama instance."""

    provider_name = "ollama"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=5.0),
        )

    def _messages(self, messages: list[LLMMessage], system_prompt: str) -> list[dict]:
        result = []
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})
        for m in messages:
            result.append({"role": m.role, "content": m.content})
        return result

    async def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        payload = {
            "model": config.model,
            "messages": self._messages(messages, config.system_prompt),
            "stream": False,
            "options": {"temperature": config.temperature, "num_predict": config.max_tokens, **config.extra},
        }
        try:
            resp = await self._client.post("/api/chat", json=payload)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc

        data = resp.json()
        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=config.model,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
        )

    async def stream(
        self, messages: list[LLMMessage], config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": config.model,
            "messages": self._messages(messages, config.system_prompt),
            "stream": True,
            "options": {"temperature": config.temperature, "num_predict": config.max_tokens, **config.extra},
        }
        try:
            async with self._client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
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
        try:
            resp = await self._client.get("/api/tags")
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]
        except Exception as exc:
            logger.warning(f"Could not list Ollama models: {exc}")
            return []
