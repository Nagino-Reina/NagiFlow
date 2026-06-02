"""Structured logging + correlation IDs (docs/05 §1, docs/12 §4).

A `correlation_id` threads request → WS turn → jobs → usage/log records. Secrets and
user message content are not logged at info level by default (docs/16 §3.3).
"""

from __future__ import annotations

import logging
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(value: str | None) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


class _CorrelationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.addFilter(_CorrelationFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-5s [%(correlation_id)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # httpx logs every outbound request at INFO; the periodic provider health probes
    # (e.g. the system-status stream pinging Ollama) would otherwise flood the log.
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
