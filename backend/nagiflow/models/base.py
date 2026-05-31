"""Declarative base + shared mixins (docs/04 §3)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    # Naive UTC to match the DB's CURRENT_TIMESTAMP server default.
    return datetime.now(UTC).replace(tzinfo=None)


class TimestampMixin:
    # Python-side `default`/`onupdate` populate the instance at flush (no refresh needed);
    # `server_default` covers raw SQL / migration inserts.
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=_utcnow,
        onupdate=_utcnow,
        server_default=func.now(),
        nullable=False,
    )
