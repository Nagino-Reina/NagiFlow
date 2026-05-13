"""
Global exception handler.

Maps NagiFlow domain exceptions to well-structured JSON HTTP responses so all
error types share a consistent envelope regardless of where they are raised.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from nagiflow.core.exceptions import NagiFlowError


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all custom exception handlers to the FastAPI application."""

    @app.exception_handler(NagiFlowError)
    async def nagiflow_error_handler(request: Request, exc: NagiFlowError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "success": False},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed.",
                "errors": exc.errors(),
                "success": False,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        import traceback
        from nagiflow.config import settings
        from loguru import logger

        logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", exc_info=True)
        detail = str(exc) if settings.DEBUG else "An internal server error occurred."
        return JSONResponse(
            status_code=500,
            content={"detail": detail, "success": False},
        )
