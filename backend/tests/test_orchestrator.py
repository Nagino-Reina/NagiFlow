"""Orchestrator provider-failure handling: a ProviderError from the LLM becomes a clean
`provider.error` envelope (502), not a raw 500 (docs/03 §6, docs/05 §3)."""

from __future__ import annotations

import pytest

from nagiflow.core.errors import AppError
from nagiflow.providers.base import GenChunk, LLMCaps, ProviderError
from nagiflow.providers.registry import ProviderRegistry
from nagiflow.services.orchestrator import DialogueOrchestrator

_BIG_FIVE = {
    "openness": 50,
    "conscientiousness": 50,
    "extraversion": 50,
    "agreeableness": 50,
    "neuroticism": 50,
}


class _FailingLLM:
    name = "ollama"
    capabilities = LLMCaps()

    async def generate(self, req):
        raise ProviderError("model 'llama3.2' not found")
        yield GenChunk()  # unreachable — makes this an async generator

    async def list_models(self):
        return []

    async def health(self):
        return False


class _Char:
    persona = "You are Aria."
    big_five = _BIG_FIVE


async def test_provider_error_maps_to_envelope():
    reg = ProviderRegistry()
    reg.register_llm(_FailingLLM(), default=True)
    orch = DialogueOrchestrator(reg)

    with pytest.raises(AppError) as excinfo:
        await orch.handle_turn(character=_Char(), history=[], user_text="hi")

    assert excinfo.value.code == "provider.error"
    assert excinfo.value.status_code == 502
    assert "llama3.2" in excinfo.value.message
