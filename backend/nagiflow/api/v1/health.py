"""Health check and system information endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from nagiflow.api.deps import require_minimum_role
from nagiflow.config import settings
from nagiflow.core.database import get_session
from nagiflow.core.security import UserRole
from nagiflow.plugin.loader import plugin_loader
from nagiflow.plugin.registry import registry

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str


class SystemInfoResponse(BaseModel):
    version: str
    database: str
    default_llm_provider: str
    default_llm_model: str
    default_tts_provider: str
    loaded_plugins: list[str]
    registered_skills: list[str]
    llm_healthy: bool
    tts_healthy: bool
    db_healthy: bool


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Lightweight liveness probe."""
    return HealthResponse(status="ok", version=settings.APP_VERSION)


@router.get(
    "/system",
    response_model=SystemInfoResponse,
    dependencies=[Depends(require_minimum_role(UserRole.ADMIN))],
)
async def system_info(db: AsyncSession = Depends(get_session)) -> SystemInfoResponse:
    """Detailed system and provider health status. Admin only."""
    # DB ping
    db_healthy = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_healthy = False

    # LLM health
    llm_healthy = True
    try:
        provider = registry.get_llm()
        llm_healthy = await provider.health_check()
    except Exception:
        llm_healthy = False

    # TTS health
    tts_healthy = True
    try:
        tts = registry.get_tts()
        tts_healthy = await tts.health_check()
    except Exception:
        tts_healthy = False

    return SystemInfoResponse(
        version=settings.APP_VERSION,
        database=settings.DATABASE_URL.split("://")[0],
        default_llm_provider=settings.DEFAULT_LLM_PROVIDER,
        default_llm_model=settings.DEFAULT_LLM_MODEL,
        default_tts_provider=settings.DEFAULT_TTS_PROVIDER,
        loaded_plugins=plugin_loader.loaded_names(),
        registered_skills=[cls.meta.name for cls in registry.list_skills()],
        llm_healthy=llm_healthy,
        tts_healthy=tts_healthy,
        db_healthy=db_healthy,
    )
