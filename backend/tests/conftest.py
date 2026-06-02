"""Shared test fixtures.

An isolated workspace + offline providers are configured via env **before** settings are
built, so the suite never touches a real DB or reaches Ollama. The `client` fixture serves
the ASGI app over httpx; lifespan does not run under ASGITransport, so the registry is
attached and the schema is created (via `init_db`) explicitly.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest_asyncio

_TMP_WORKSPACE = tempfile.mkdtemp(prefix="nagiflow-test-")
os.environ["NAGIFLOW_WORKSPACE_DIR"] = _TMP_WORKSPACE
os.environ["NAGIFLOW_DEFAULT_LLM"] = "echo"
os.environ["NAGIFLOW_DEFAULT_TTS"] = "silent"
os.environ["NAGIFLOW_AFFECT_APPRAISAL"] = "deterministic"


@pytest_asyncio.fixture
async def client():
    from httpx import ASGITransport, AsyncClient

    from nagiflow.config import get_settings
    from nagiflow.core import database
    from nagiflow.main import create_app
    from nagiflow.providers.registry import build_registry

    from nagiflow.models.base import Base

    get_settings.cache_clear()
    await database.dispose_db()  # drop any engine bound to earlier settings

    settings = get_settings()
    Path(settings.workspace_dir).mkdir(parents=True, exist_ok=True)

    # Fresh schema per test for isolation (the temp DB file persists across the session).
    import nagiflow.models  # noqa: F401 — register all tables on the metadata

    engine = database.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    app = create_app()
    app.state.registry = build_registry(settings)  # lifespan is not run under ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await database.dispose_db()
