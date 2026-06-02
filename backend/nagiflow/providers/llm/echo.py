"""Offline echo LLM (docs/06 §12 fallback).

No external dependency — lets the whole stack run without Ollama installed. Produces a
deterministic, persona-aware reply so the chat pipeline is demonstrable end-to-end.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from ..base import GenChunk, GenRequest, GenUsage, LLMCaps


class EchoLLM:
    name = "echo"
    model: str | None = None
    capabilities = LLMCaps(streaming=True, tools=False, context_window=8192)

    async def generate(self, req: GenRequest) -> AsyncIterator[GenChunk]:
        last_user = next((m.content for m in reversed(req.messages) if m.role == "user"), "")
        reply = f"(echo) You said: {last_user}" if last_user else "(echo) Hello!"
        for word in reply.split(" "):
            yield GenChunk(delta=word + " ")
        yield GenChunk(
            done=True,
            usage=GenUsage(prompt_tokens=0, completion_tokens=len(reply.split())),
        )

    async def list_models(self) -> list[str]:
        return ["echo"]

    async def health(self) -> bool:
        return True
