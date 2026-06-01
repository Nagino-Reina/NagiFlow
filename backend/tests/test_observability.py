"""Observability: usage accounting (FR-OBS-3) + system resources (FR-OBS-1) over HTTP."""

from __future__ import annotations

API = "/api/v1"


async def _user_headers(client) -> dict[str, str]:
    await client.post(f"{API}/auth/register", json={"username": "obs", "password": "password123"})
    login = await client.post(
        f"{API}/auth/login", json={"username": "obs", "password": "password123"}
    )
    return {"Authorization": f"Bearer {login.json()['token']}"}


async def _chat_once(client, headers) -> None:
    char = await client.post(
        f"{API}/characters", headers=headers, json={"name": "Aria", "guest_visible": True}
    )
    conv = await client.post(
        f"{API}/conversations", headers=headers, json={"character_id": char.json()["id"]}
    )
    await client.post(
        f"{API}/conversations/{conv.json()['id']}/messages",
        headers=headers,
        json={"text": "Hello!"},
    )


async def test_usage_recorded_for_reply_and_tts(client):
    headers = await _user_headers(client)
    await _chat_once(client, headers)

    res = await client.get(f"{API}/usage:summary", headers=headers)
    assert res.status_code == 200, res.text
    summary = res.json()

    # One LLM call + one TTS call were recorded for the single turn.
    assert summary["totals"]["calls"] == 2
    providers = {g["key"] for g in summary["by_provider"]}
    assert {"echo", "silent"} <= providers
    assert len(summary["by_day"]) >= 1
    assert any(g["key"] for g in summary["by_character"])


async def test_usage_list_is_scoped_to_user(client):
    headers = await _user_headers(client)
    await _chat_once(client, headers)

    mine = await client.get(f"{API}/usage", headers=headers)
    assert mine.status_code == 200
    assert mine.json()["totals"]["calls"] == 2
    assert len(mine.json()["records"]) == 2

    # A different (guest) principal sees none of it.
    guest = await client.post(f"{API}/auth/guest")
    guest_headers = {"Authorization": f"Bearer {guest.json()['token']}"}
    other = await client.get(f"{API}/usage", headers=guest_headers)
    assert other.status_code == 403  # guest is gated out of usage entirely (RequireUser)


async def test_system_resources_snapshot(client):
    headers = await _user_headers(client)
    res = await client.get(f"{API}/system/resources", headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["memory"]["total"] > 0
    assert body["disk"]["total"] > 0
    assert isinstance(body["gpus"], list)
