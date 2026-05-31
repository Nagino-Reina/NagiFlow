"""API v1 router aggregation (docs/05 §1 — base path /api/v1)."""

from __future__ import annotations

from fastapi import APIRouter

from . import auth, characters, conversations, health, system, voice

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(characters.router)
api_router.include_router(voice.router)
api_router.include_router(conversations.router)
api_router.include_router(system.router)

# health/liveness endpoints sit at the root (no version prefix)
root_router = APIRouter()
root_router.include_router(health.router)
