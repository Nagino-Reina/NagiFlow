"""Roleplay-prompt setting over HTTP + the TTS action-stripping helper (docs/05 §4.7, docs/08 §4)."""

from __future__ import annotations

from nagiflow.services.conversation_service import spoken_text

API = "/api/v1"


async def _auth_headers(client) -> dict[str, str]:
    await client.post(
        f"{API}/auth/register", json={"username": "tester", "password": "password123"}
    )
    login = await client.post(
        f"{API}/auth/login", json={"username": "tester", "password": "password123"}
    )
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_spoken_text_strips_action_directions() -> None:
    assert spoken_text("Hello there. (smiles) How are you?") == "Hello there. How are you?"
    assert spoken_text("（轉身）你好") == "你好"
    assert spoken_text("*waves* hi") == "hi"
    assert spoken_text("Just talking, no actions.") == "Just talking, no actions."


async def test_roleplay_prompt_get_set_reset(client):
    headers = await _auth_headers(client)

    got = await client.get(f"{API}/settings/roleplay-prompt", headers=headers)
    assert got.status_code == 200, got.text
    default = got.json()["default"]
    assert default and got.json()["roleplay_prompt"] == default  # no override yet

    put = await client.put(
        f"{API}/settings/roleplay-prompt", headers=headers, json={"value": "Be a pirate."}
    )
    assert put.status_code == 200, put.text
    assert put.json()["roleplay_prompt"] == "Be a pirate."

    again = await client.get(f"{API}/settings/roleplay-prompt", headers=headers)
    assert again.json()["roleplay_prompt"] == "Be a pirate."

    reset = await client.delete(f"{API}/settings/roleplay-prompt", headers=headers)
    assert reset.json()["roleplay_prompt"] == default


async def test_roleplay_prompt_requires_auth(client):
    res = await client.get(f"{API}/settings/roleplay-prompt")
    assert res.status_code == 401
