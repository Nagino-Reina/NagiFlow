"""
Test suite for NagiFlow.

Run with::

    pytest
"""

import pytest
from httpx import AsyncClient, ASGITransport


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def app():
    """Create a test application with an in-memory SQLite database."""
    import os
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")
    os.environ.setdefault("WORKSPACE_DIR", "/tmp/nagiflow_test_workspace")
    os.environ.setdefault("DEFAULT_LLM_PROVIDER", "ollama")
    os.environ.setdefault("FIRST_ADMIN_EMAIL", "")
    os.environ.setdefault("FIRST_ADMIN_PASSWORD", "")

    from nagiflow.main import create_app
    _app = create_app()

    async with _app.router.lifespan_context(_app):
        yield _app


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
async def registered_user(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
    })
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
async def auth_headers(client, registered_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_register(client):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "username": "newuser",
        "password": "securepassword",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert "id" in data


@pytest.mark.anyio
async def test_register_duplicate_email(client, registered_user):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "other",
        "password": "password123",
    })
    assert resp.status_code == 409


@pytest.mark.anyio
async def test_login(client, registered_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.anyio
async def test_login_wrong_password(client, registered_user):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_get_me(client, auth_headers):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_character(client, auth_headers):
    resp = await client.post("/api/v1/characters", headers=auth_headers, json={
        "name": "Nagi",
        "description": "A friendly AI Vtuber.",
        "personality": {
            "big_five": {
                "openness": 80,
                "conscientiousness": 60,
                "extraversion": 75,
                "agreeableness": 85,
                "neuroticism": 30,
            },
            "custom": {"catchphrase": "Let's go!"},
        },
        "is_public": False,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Nagi"
    assert data["personality"]["big_five"]["openness"] == 80
    return data


@pytest.mark.anyio
async def test_list_characters(client, auth_headers):
    # Create one first
    await test_create_character(client, auth_headers)
    resp = await client.get("/api/v1/characters", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.anyio
async def test_update_character(client, auth_headers):
    char = await test_create_character(client, auth_headers)
    char_id = char["id"]
    resp = await client.patch(
        f"/api/v1/characters/{char_id}",
        headers=auth_headers,
        json={"name": "Nagi Updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Nagi Updated"


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_skills(client, auth_headers):
    resp = await client.get("/api/v1/skills", headers=auth_headers)
    assert resp.status_code == 200
    skills = resp.json()
    names = [s["name"] for s in skills]
    assert "web_search" in names
    assert "calculator" in names


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_memory(client, auth_headers):
    char = await test_create_character(client, auth_headers)
    char_id = char["id"]
    resp = await client.post(
        f"/api/v1/characters/{char_id}/memories",
        headers=auth_headers,
        json={"content": "The user's favourite game is Minecraft.", "importance": 7.5},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "The user's favourite game is Minecraft."


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_create_knowledge_doc(client, auth_headers):
    resp = await client.post(
        "/api/v1/knowledge",
        headers=auth_headers,
        json={
            "title": "NagiFlow Docs",
            "content": "NagiFlow is an AI Vtuber framework. " * 10,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "NagiFlow Docs"


# ---------------------------------------------------------------------------
# Security: text chunking unit test
# ---------------------------------------------------------------------------


def test_chunk_text_empty():
    from nagiflow.services.knowledge import chunk_text
    assert chunk_text("") == []


def test_chunk_text_short():
    from nagiflow.services.knowledge import chunk_text
    assert chunk_text("Hello world.") == ["Hello world."]


def test_chunk_text_long():
    from nagiflow.services.knowledge import chunk_text
    text = "This is a sentence. " * 100
    chunks = chunk_text(text, chunk_size=200, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 220 for c in chunks)


def test_calculator_skill_safe():
    import asyncio
    from nagiflow.skills.builtin.calculator import CalculatorSkill
    skill = CalculatorSkill()
    result = asyncio.run(skill.execute(expression="sqrt(16) + 2 * pi"))
    assert "10" in result or "10." in result


def test_calculator_skill_invalid():
    import asyncio
    from nagiflow.skills.builtin.calculator import CalculatorSkill
    skill = CalculatorSkill()
    result = asyncio.run(skill.execute(expression="import os"))
    assert "error" in result.lower()
