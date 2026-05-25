"""Provider registry introspection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from nagiflow.api.deps import get_current_user
from nagiflow.models.user import User
from nagiflow.plugin.registry import registry

router = APIRouter(prefix="/providers", tags=["providers"])


class ProvidersResponse(BaseModel):
    llm: list[str]
    tts: list[str]
    avatar: list[str]
    embedding: list[str]
    skills: list[str]


@router.get("/", response_model=ProvidersResponse)
async def list_providers(
    _: User = Depends(get_current_user),
) -> ProvidersResponse:
    """List all currently registered providers grouped by type."""
    summary = registry.summary()
    return ProvidersResponse(**summary)


@router.get("/{provider_type}/health")
async def provider_health(
    provider_type: str,
    name: str | None = None,
    _: User = Depends(get_current_user),
) -> dict:
    """
    Basic health check for a provider type.
    Optional query param ``name`` selects a specific provider within the type.
    """
    available: dict[str, list[str]] = {
        "llm": registry.list_llm(),
        "tts": registry.list_tts(),
        "avatar": registry.list_avatar(),
        "embedding": registry.list_embedding(),
    }
    if provider_type not in available:
        return {"ok": False, "error": f"Unknown provider type '{provider_type}'"}

    providers = available[provider_type]
    if name and name not in providers:
        return {"ok": False, "error": f"Provider '{name}' not registered"}

    return {
        "ok": True,
        "type": provider_type,
        "registered": providers,
        "selected": name or "(default)",
    }
