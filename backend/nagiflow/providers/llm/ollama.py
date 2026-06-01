"""Default LLM provider via a local Ollama server (docs/06 §12).

Streaming chat over Ollama's `/api/chat`. Provider failures are surfaced (health()/errors)
rather than crashing the request — the registry can fall back (docs/03 §6).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ..base import ChatMessage, GenChunk, GenRequest, GenUsage, LLMCaps, ProviderError


class OllamaLLM:
    name = "ollama"
    capabilities = LLMCaps(streaming=True, tools=True, embeddings=True, context_window=8192)

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    def _payload(self, req: GenRequest) -> dict:
        return {
            "model": req.model or self._model,
            "messages": [{"role": _role(m), "content": m.content} for m in req.messages],
            "stream": True,
            "options": {"temperature": req.temperature},
        }

    async def generate(self, req: GenRequest) -> AsyncIterator[GenChunk]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=5.0)) as client:
                async with client.stream(
                    "POST", f"{self._base_url}/api/chat", json=self._payload(req)
                ) as resp:
                    if resp.status_code >= 400:
                        # Read the body for a useful message (e.g. model-not-found 404).
                        body = (await resp.aread()).decode("utf-8", "replace").strip()
                        raise ProviderError(
                            f"Ollama /api/chat returned {resp.status_code}: {body[:200]}"
                        )
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise ProviderError(f"Ollama sent invalid JSON: {exc}") from exc
                        if data.get("done"):
                            yield GenChunk(
                                done=True,
                                usage=GenUsage(
                                    prompt_tokens=data.get("prompt_eval_count"),
                                    completion_tokens=data.get("eval_count"),
                                ),
                            )
                            return
                        delta = data.get("message", {}).get("content", "")
                        if delta:
                            yield GenChunk(delta=delta)
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"Could not reach Ollama at {self._base_url} (model '{self._model}'): {exc}"
            ) from exc

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{self._base_url}/api/tags")
            resp.raise_for_status()
            return [m["name"] for m in resp.json().get("models", [])]

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self._base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False


def _role(m: ChatMessage) -> str:
    # NagiFlow uses "character"; Ollama expects "assistant".
    return "assistant" if m.role in ("character", "assistant") else m.role
