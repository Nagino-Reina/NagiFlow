"""System & service-health endpoints (docs/05 §4.7, docs/11 §2.2)."""

from __future__ import annotations

from fastapi import APIRouter

from ... import __version__
from ...config import get_settings
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


@router.get("/services")
async def services(_user: RequireUser, registry: Registry) -> dict[str, list[dict]]:
    llm = registry.get_llm()
    healthy = await llm.health()
    return {
        "services": [
            {
                "capability": "llm",
                "name": llm.name,
                "status": "up" if healthy else "down",
            }
        ]
    }
