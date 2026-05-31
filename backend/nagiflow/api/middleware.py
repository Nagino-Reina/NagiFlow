"""Correlation-ID middleware (docs/05 §1, docs/11 §4)."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..core.ids import new_id
from ..core.logging import set_correlation_id

HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        cid = request.headers.get(HEADER) or new_id("req")
        set_correlation_id(cid)
        request.state.correlation_id = cid
        response = await call_next(request)
        response.headers[HEADER] = cid
        return response
