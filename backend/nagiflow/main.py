"""FastAPI application factory (docs/03 §2, §3.3).

Wires middleware (correlation, CORS), routers, the error envelope, providers, and the
DB lifespan. In prod the built SPA is served by this same process (docs/03 ADR-006) — that
static mount lands with the runtime/launcher work (docs/13).
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import __version__
from .api.middleware import CorrelationIdMiddleware
from .api.v1 import api_router, root_router
from .config import get_settings
from .core.database import dispose_db
from .core.errors import AppError
from .core.logging import configure_logging, get_correlation_id, get_logger
from .core.migrations import run_migrations
from .core.workspace import Workspace
from .providers.registry import build_registry

log = get_logger("nagiflow.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    Workspace(settings.workspace_dir).ensure()
    app.state.registry = build_registry(settings)
    await asyncio.to_thread(run_migrations)
    log.info("NagiFlow %s started (workspace=%s)", __version__, settings.workspace_dir)
    yield
    await dispose_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="NagiFlow", version=__version__, lifespan=lifespan)

    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(root_router)
    app.include_router(api_router)

    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content=exc.envelope(get_correlation_id())
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        err = AppError(
            "validation.failed",
            "Request validation failed.",
            status_code=422,
            details={"errors": exc.errors()},
        )
        return JSONResponse(status_code=422, content=err.envelope(get_correlation_id()))

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error")
        err = AppError("internal.error", "Internal server error.", status_code=500)
        return JSONResponse(status_code=500, content=err.envelope(get_correlation_id()))

    return app


app = create_app()
