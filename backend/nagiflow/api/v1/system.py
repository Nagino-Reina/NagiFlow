"""System resource & service-health endpoints (docs/05 §4.7, §5.1, docs/12 §2)."""

from __future__ import annotations

import asyncio
from datetime import date, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ... import __version__
from ...config import get_settings
from ...core.database import get_sessionmaker
from ...core.logging import get_logger
from ...core.sysinfo import resource_snapshot
from ...providers.registry import ProviderRegistry
from ...repositories.usage import UsageRepository
from ...repositories.users import SessionRepository, UserRepository
from ...schemas.observability import SystemResources
from ...services.auth_service import AuthService, Principal
from ...services.usage_service import UsageService
from ..deps import COOKIE_NAME, CurrentPrincipal, Registry, RequireUser

log = get_logger("nagiflow.system")

router = APIRouter(prefix="/system", tags=["system"])


async def _service_statuses(registry: ProviderRegistry) -> list[dict]:
    """Per-capability provider health, probed concurrently so a slow/down provider does
    not serialize the others (docs/05 §4.7)."""
    llm, tts = registry.get_llm(), registry.get_tts()
    llm_up, tts_up = await asyncio.gather(llm.health(), tts.health())
    return [
        {
            "capability": cap,
            "name": provider.name,
            "model": getattr(provider, "model", None),
            "status": "up" if up else "down",
        }
        for cap, provider, up in (("llm", llm, llm_up), ("tts", tts, tts_up))
    ]


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
    return {"services": await _service_statuses(registry)}


def _jsonable(obj: object) -> object:
    """Recursively coerce a value to something `send_json` can serialize, and never raise.

    Backend libraries (psutil/pynvml/torch) can surface numpy scalars/arrays that the default
    JSON encoder rejects; numpy is also an optional dependency, so it is detected by duck typing
    rather than imported. Anything unrecognized degrades to its string form instead of crashing
    the status stream (docs/05 §5.1)."""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {_jsonable(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_jsonable(v) for v in obj]
    if hasattr(obj, "dtype"):  # numpy scalar (.item()) or array (.tolist())
        return obj.item() if hasattr(obj, "item") and obj.ndim == 0 else obj.tolist()
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)


async def _status_snapshot(registry: ProviderRegistry, user_id: str) -> dict:
    """Combined resources + service health + usage summary for one stream tick (docs/05 §5.1).

    Usage runs in its own short-lived session so the stream never holds a DB connection (and
    thus the SQLite writer) open between ticks. Returned JSON-ready for `send_json`.
    """
    settings = get_settings()
    services_out = await _service_statuses(registry)
    resources = SystemResources.model_validate(
        resource_snapshot(settings.workspace_dir)
    ).model_dump()
    async with get_sessionmaker()() as session:
        usage = await UsageService(UsageRepository(session)).summary(user_id)
    return _jsonable(
        {
            "type": "system.status",
            "resources": resources,
            "services": services_out,
            "usage": usage,
        }
    )


def _stream_token(websocket: WebSocket) -> tuple[str | None, bool]:
    """Resolve the session token from the bearer sub-protocol or the session cookie, never a
    query string (docs/05 §5). Returns (token, used_subprotocol)."""
    protocols = websocket.scope.get("subprotocols") or []
    if len(protocols) >= 2 and protocols[0] == "bearer":
        return protocols[1], True
    return websocket.cookies.get(COOKIE_NAME), False


async def _resolve_ws(token: str | None) -> Principal | None:
    if not token:
        return None
    async with get_sessionmaker()() as session:
        auth = AuthService(UserRepository(session), SessionRepository(session))
        return await auth.resolve(token)


@router.websocket("/stream")
async def system_stream(websocket: WebSocket) -> None:
    """Push system status (resources, service health, usage) on an interval (docs/05 §5.1).

    Replaces REST polling: one connection, authenticated once at connect, so the bar stays
    live without a timer hammering several endpoints (and without per-poll session writes).
    """
    token, used_subprotocol = _stream_token(websocket)
    principal = await _resolve_ws(token)
    if principal is None or principal.kind != "user":
        # 1008 = policy violation; the client treats it as "do not reconnect".
        await websocket.close(code=1008)
        return

    await websocket.accept(subprotocol="bearer" if used_subprotocol else None)
    registry: ProviderRegistry = websocket.app.state.registry
    interval = get_settings().status_stream_interval
    try:
        while True:
            await websocket.send_json(await _status_snapshot(registry, principal.user_id))
            await asyncio.sleep(interval)
    except WebSocketDisconnect:
        return
    except Exception:  # noqa: BLE001 — never let a transient snapshot error kill the worker
        log.exception("system stream failed")
        await websocket.close(code=1011)  # internal error
