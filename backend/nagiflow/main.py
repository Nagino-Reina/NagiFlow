"""
NagiFlow – AI Vtuber streaming framework.

Application factory and entry point.

Run in development::

    uvicorn nagiflow.main:app --reload

Or via the CLI::

    nagiflow

Or via Python::

    python -m nagiflow.main
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from nagiflow.api.exception_handlers import register_exception_handlers
from nagiflow.config import settings
from nagiflow.core.database import create_all_tables, dispose_engine, session_context
from nagiflow.core.workspace import workspace
from nagiflow.plugin.loader import plugin_loader
from nagiflow.plugin.registry import registry
from nagiflow.services.auth import AuthService


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown logic."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} …")

    # 1. Ensure workspace directories exist (sync, fast)
    workspace.ensure_structure()

    # 2. Create / migrate database tables
    await create_all_tables()

    # 3. Load all plugins (built-in + user workspace)
    await plugin_loader.load_all(workspace.plugins_dir())

    # 4. Sync registered skills to DB
    async with session_context() as db:
        await registry.sync_skills_to_db(db)

    # 5. Bootstrap first admin account (no-op if users already exist)
    async with session_context() as db:
        auth_svc = AuthService(db)
        await auth_svc.ensure_admin(
            settings.FIRST_ADMIN_EMAIL, settings.FIRST_ADMIN_PASSWORD
        )

    logger.info("NagiFlow is ready.")
    yield

    # Shutdown
    logger.info("Shutting down NagiFlow …")
    await plugin_loader.unload_all()
    await dispose_engine()
    logger.info("Goodbye.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "An extensible AI Vtuber streaming framework supporting LLM, TTS, "
            "Live2D / 3D character models, long-term memory, RAG knowledge base, "
            "and a modular plugin / skill system."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    register_exception_handlers(app)

    # Routers
    from nagiflow.api.v1.auth import router as auth_router
    from nagiflow.api.v1.audio import router as audio_router
    from nagiflow.api.v1.characters import router as characters_router
    from nagiflow.api.v1.conversations import router as conversations_router
    from nagiflow.api.v1.health import router as health_router
    from nagiflow.api.v1.knowledge import router as knowledge_router
    from nagiflow.api.v1.memory import router as memory_router
    from nagiflow.api.v1.providers import router as providers_router
    from nagiflow.api.v1.scripts import router as scripts_router
    from nagiflow.api.v1.skills import router as skills_router
    from nagiflow.api.v1.streaming import router as streaming_router
    from nagiflow.api.v1.training import router as training_router
    from nagiflow.api.v1.users import router as users_router

    prefix = "/api/v1"
    app.include_router(health_router, prefix=prefix)
    app.include_router(auth_router, prefix=prefix)
    app.include_router(users_router, prefix=prefix)
    app.include_router(characters_router, prefix=prefix)
    app.include_router(conversations_router, prefix=prefix)
    app.include_router(memory_router, prefix=prefix)
    app.include_router(knowledge_router, prefix=prefix)
    app.include_router(skills_router, prefix=prefix)
    app.include_router(audio_router, prefix=prefix)
    app.include_router(streaming_router, prefix=prefix)
    app.include_router(scripts_router, prefix=prefix)
    app.include_router(training_router, prefix=prefix)
    app.include_router(providers_router, prefix=prefix)

    return app


app = create_app()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run() -> None:
    """CLI entry point (``nagiflow`` command)."""
    uvicorn.run(
        "nagiflow.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )


if __name__ == "__main__":
    run()
