"""OpenAI-compatible LLM provider implementation."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

import httpx
from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import LLMProviderError
from nagiflow.plugin.base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse


class OpenAICompatProvider(BaseLLMProvider):
    """LLM provider for any OpenAI-compatible REST API."""

    provider_name = "openai_compat"

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=5.0),
        )

    def _payload(self, messages: list[LLMMessage], config: LLMConfig, stream: bool) -> dict:
        oai_msgs = []
        if config.system_prompt:
            oai_msgs.append({"role": "system", "content": config.system_prompt})
        for m in messages:
            oai_msgs.append({"role": m.role, "content": m.content})
        return {
            "model": config.model,
            "messages": oai_msgs,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": stream,
            **config.extra,
        }

    async def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        try:
            resp = await self._client.post("/chat/completions", json=self._payload(messages, config, False))
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"OpenAI-compat request failed: {exc}") from exc

        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})
        return LLMResponse(
            content=choice["message"]["content"] or "",
            model=data.get("model", config.model),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
        )

    async def stream(
        self, messages: list[LLMMessage], config: LLMConfig
    ) -> AsyncGenerator[str, None]:
        try:
            async with self._client.stream("POST", "/chat/completions", json=self._payload(messages, config, True)) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or line == "data: [DONE]":
                        continue
                    if line.startswith("data: "):
                        line = line[6:]
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk["choices"][0].get("delta", {}).get("content") or ""
                    if delta:
                        yield delta
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"OpenAI-compat stream failed: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            resp = await self._client.get("/models", timeout=5.0)
            return resp.is_success
        except Exception as exc:
            logger.warning(f"OpenAI-compat health check failed: {exc}")
            return False
