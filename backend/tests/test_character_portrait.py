"""Character portrait upload/fetch/clear over HTTP (docs/05 §4.1, FR-CM-2).

Runs fully offline (temp workspace + offline providers, see conftest). Guards the
`has_portrait` flag, the stored-file round-trip, and rejection of non-image uploads.
"""

from __future__ import annotations

API = "/api/v1"

# A minimal valid 1x1 PNG.
_PNG_1x1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c6360000002000154a24f5f0000000049454e44ae426082"
)


async def _auth_headers(client) -> dict[str, str]:
    await client.post(
        f"{API}/auth/register", json={"username": "tester", "password": "password123"}
    )
    login = await client.post(
        f"{API}/auth/login", json={"username": "tester", "password": "password123"}
    )
    return {"Authorization": f"Bearer {login.json()['token']}"}


async def _make_character(client, headers) -> str:
    res = await client.post(
        f"{API}/characters",
        headers=headers,
        json={"name": "Aria", "guest_visible": True},
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def test_portrait_upload_fetch_clear(client):
    headers = await _auth_headers(client)
    cid = await _make_character(client, headers)

    created = await client.get(f"{API}/characters/{cid}", headers=headers)
    assert created.json()["has_portrait"] is False

    up = await client.put(
        f"{API}/characters/{cid}/portrait",
        headers=headers,
        files={"file": ("p.png", _PNG_1x1, "image/png")},
    )
    assert up.status_code == 200, up.text
    assert up.json()["has_portrait"] is True

    dl = await client.get(f"{API}/characters/{cid}/portrait", headers=headers)
    assert dl.status_code == 200, dl.text
    assert dl.headers["content-type"] == "image/png"
    assert dl.content[:8] == _PNG_1x1[:8]

    cleared = await client.delete(f"{API}/characters/{cid}/portrait", headers=headers)
    assert cleared.status_code == 204
    after = await client.get(f"{API}/characters/{cid}", headers=headers)
    assert after.json()["has_portrait"] is False
    assert (
        await client.get(f"{API}/characters/{cid}/portrait", headers=headers)
    ).status_code == 404


async def test_portrait_rejects_unsupported_type(client):
    headers = await _auth_headers(client)
    cid = await _make_character(client, headers)
    res = await client.put(
        f"{API}/characters/{cid}/portrait",
        headers=headers,
        files={"file": ("note.txt", b"not an image", "text/plain")},
    )
    assert res.status_code == 415, res.text
