"""
OpenAI-compatible LLM provider.

Works with any endpoint that implements the OpenAI Chat Completions API,
including OpenAI itself, Azure OpenAI, local LM Studio, vLLM, etc.
"""

from collections.abc import AsyncGenerator

import httpx
from loguru import logger

from nagiflow.config import settings
from nagiflow.core.exceptions import LLMProviderError
from nagiflow.llm.base import BaseLLMProvider, LLMConfig, LLMMessage, LLMResponse


class OpenAICompatProvider(BaseLLMProvider):
    """
    LLM provider for any OpenAI-compatible REST API.

    Configure via environment variables::

        DEFAULT_LLM_PROVIDER=openai_compat
        OPENAI_BASE_URL=https://api.openai.com/v1
        OPENAI_API_KEY=sk-...
        DEFAULT_LLM_MODEL=gpt-4o
    """

    provider_name = "openai_compat"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.OPENAI_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=5.0),
        )

    def _build_payload(
        self, messages: list[LLMMessage], config: LLMConfig, stream: bool
    ) -> dict:
        oai_messages = []
        if config.system_prompt:
            oai_messages.append({"role": "system", "content": config.system_prompt})
        for m in messages:
            oai_messages.append({"role": m.role, "content": m.content})

        return {
            "model": config.model,
            "messages": oai_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "stream": stream,
            **config.extra,
        }

    async def generate(self, messages: list[LLMMessage], config: LLMConfig) -> LLMResponse:
        payload = self._build_payload(messages, config, stream=False)
        try:
            resp = await self._client.post("/chat/completions", json=payload)
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
        import json

        payload = self._build_payload(messages, config, stream=True)
        try:
            async with self._client.stream("POST", "/chat/completions", json=payload) as resp:
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
