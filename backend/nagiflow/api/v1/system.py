"""System resource & service-health endpoints (docs/05 §4.7, docs/12 §2)."""

from __future__ import annotations

from fastapi import APIRouter

from ... import __version__
from ...config import get_settings
from ...core.sysinfo import resource_snapshot
from ...schemas.observability import SystemResources
from ..deps import CurrentPrincipal, Registry, RequireUser

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info")
async def info(_principal: CurrentPrincipal) -> dict[str, str]:
    settings = get_settings()
    return {
        "name": "NagiFlow",
        "version": __version__,
        "workspace": str(settings.workspace_dir),
    }


@router.get("/resources", response_model=SystemResources)
async def resources(_user: RequireUser) -> SystemResources:
    return SystemResources.model_validate(resource_snapshot(get_settings().workspace_dir))


@router.get("/services")
async def services(_user: RequireUser, registry: Registry) -> dict[str, list[dict]]:
    services_out: list[dict] = []
    for capability, provider in (("llm", registry.get_llm()), ("tts", registry.get_tts())):
        healthy = await provider.health()
        services_out.append(
            {
                "capability": capability,
                "name": provider.name,
                "status": "up" if healthy else "down",
            }
        )
    return {"services": services_out}
