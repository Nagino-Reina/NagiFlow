"""End-to-end chat flow over HTTP (docs/05 §4.3): register → login → create character →
create conversation → send a message → list messages.

Runs fully offline (echo LLM, deterministic affect). Guards the synchronous-turn
serialization path — notably that `created_at` is populated before the response is
validated (it is a flush-time default, not set at construction).
"""

from __future__ import annotations

API = "/api/v1"


async def _auth_headers(client) -> dict[str, str]:
    reg = await client.post(
        f"{API}/auth/register", json={"username": "tester", "password": "password123"}
    )
    assert reg.status_code == 201, reg.text
    login = await client.post(
        f"{API}/auth/login", json={"username": "tester", "password": "password123"}
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['token']}"}


async def _make_character(client, headers) -> str:
    res = await client.post(
        f"{API}/characters",
        headers=headers,
        json={"name": "Aria", "persona": "You are Aria, warm and brief.", "guest_visible": True},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def test_create_conversation_populates_created_at(client):
    headers = await _auth_headers(client)
    character_id = await _make_character(client, headers)

    res = await client.post(
        f"{API}/conversations", headers=headers, json={"character_id": character_id}
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["created_at"], "created_at must be populated (flush-time default)"
    assert body["character_id"] == character_id
    assert body["status"] == "active"


async def test_send_message_returns_reply_with_affect(client):
    headers = await _auth_headers(client)
    character_id = await _make_character(client, headers)
    conv = (
        await client.post(
            f"{API}/conversations", headers=headers, json={"character_id": character_id}
        )
    ).json()

    empty = await client.get(f"{API}/conversations/{conv['id']}/messages", headers=headers)
    assert empty.status_code == 200 and empty.json() == []

    sent = await client.post(
        f"{API}/conversations/{conv['id']}/messages",
        headers=headers,
        json={"text": "Hello there!"},
    )
    assert sent.status_code == 200, sent.text
    payload = sent.json()

    user_msg, reply = payload["user_message"], payload["reply"]
    assert user_msg["role"] == "user" and user_msg["content"] == "Hello there!"
    assert user_msg["created_at"] and reply["created_at"]
    assert reply["role"] == "character" and reply["content"]
    # affect snapshot rides on the reply meta (docs/10 §8)
    assert "affect" in reply["meta"] and reply["meta"]["affect"]["source"] == "fallback"

    history = await client.get(f"{API}/conversations/{conv['id']}/messages", headers=headers)
    assert history.status_code == 200 and len(history.json()) == 2


async def test_reply_audio_is_synthesized_and_downloadable(client):
    headers = await _auth_headers(client)
    character_id = await _make_character(client, headers)
    conv = (
        await client.post(
            f"{API}/conversations", headers=headers, json={"character_id": character_id}
        )
    ).json()

    reply = (
        await client.post(
            f"{API}/conversations/{conv['id']}/messages", headers=headers, json={"text": "Hi!"}
        )
    ).json()["reply"]

    media_id = reply["media_asset_id"]
    assert media_id, "silent TTS always synthesizes reply audio (docs/11 §4.6)"

    dl = await client.get(f"{API}/media/{media_id}:download", headers=headers)
    assert dl.status_code == 200, dl.text
    assert dl.headers["content-type"] == "audio/wav"
    assert dl.content[:4] == b"RIFF"

    # another user cannot download it
    guest = await client.post(f"{API}/auth/guest")
    guest_headers = {"Authorization": f"Bearer {guest.json()['token']}"}
    forbidden = await client.get(f"{API}/media/{media_id}:download", headers=guest_headers)
    assert forbidden.status_code == 403


async def test_delete_conversation(client):
    headers = await _auth_headers(client)
    character_id = await _make_character(client, headers)
    conv = (
        await client.post(
            f"{API}/conversations", headers=headers, json={"character_id": character_id}
        )
    ).json()
    await client.post(
        f"{API}/conversations/{conv['id']}/messages", headers=headers, json={"text": "hi"}
    )

    res = await client.delete(f"{API}/conversations/{conv['id']}", headers=headers)
    assert res.status_code == 204, res.text

    listed = await client.get(f"{API}/conversations", headers=headers)
    assert all(c["id"] != conv["id"] for c in listed.json())

    gone = await client.get(f"{API}/conversations/{conv['id']}/messages", headers=headers)
    assert gone.status_code == 404


async def test_send_message_rejects_other_users_conversation(client):
    headers = await _auth_headers(client)
    character_id = await _make_character(client, headers)
    conv = (
        await client.post(
            f"{API}/conversations", headers=headers, json={"character_id": character_id}
        )
    ).json()

    guest = await client.post(f"{API}/auth/guest")
    guest_headers = {"Authorization": f"Bearer {guest.json()['token']}"}
    res = await client.post(
        f"{API}/conversations/{conv['id']}/messages",
        headers=guest_headers,
        json={"text": "not mine"},
    )
    assert res.status_code == 403, res.text
