"""Async SQLAlchemy engine + session (docs/04 §3).

SQLite in WAL mode (concurrent readers, resilience); `busy_timeout` to avoid
SQLITE_BUSY under live turns + jobs (docs/04 §3 write-concurrency note). Foreign keys on.

Schema is owned by Alembic migrations (docs/14 §6); the app upgrades to `head` on boot
(`core.migrations`). `init_db` (`create_all`) remains for tests/fixtures only. The
repository + unit-of-work pattern lives in `repositories/`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import get_settings
from ..models.base import Base

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _configure_sqlite(dbapi_conn, _record) -> None:  # noqa: ANN001
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA busy_timeout=15000")
    cur.close()


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(settings.db_url, echo=settings.debug, future=True)
        event.listen(_engine.sync_engine, "connect", _configure_sqlite)
        _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def init_db() -> None:
    """Create tables directly from metadata. Tests/fixtures only — runtime uses Alembic."""
    engine = get_engine()
    # Import models so they register on Base.metadata before create_all.
    from .. import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_db() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: a transactional session (unit-of-work per request)."""
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
