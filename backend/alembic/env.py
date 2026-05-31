"""Alembic environment (docs/13 §6).

Uses a synchronous SQLite engine derived from NagiFlow settings; `render_as_batch=True`
enables SQLite-friendly ALTERs. Targets `Base.metadata` for autogenerate.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine, pool

from nagiflow.config import get_settings
from nagiflow.models import Base

target_metadata = Base.metadata


def _url() -> str:
    return f"sqlite:///{get_settings().db_path.as_posix()}"


def run_migrations_offline() -> None:
    context.configure(
        url=_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
