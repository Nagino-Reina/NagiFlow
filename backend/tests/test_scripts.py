"""Script authoring over HTTP (docs/05 §4.2, FR-SM-1/2/3/4): CRUD, lines, reorder, validate."""

from __future__ import annotations

API = "/api/v1"


async def _auth_headers(client) -> dict[str, str]:
    await client.post(
        f"{API}/auth/register", json={"username": "tester", "password": "password123"}
    )
    login = await client.post(
        f"{API}/auth/login", json={"username": "tester", "password": "password123"}
    )
    return {"Authorization": f"Bearer {login.json()['token']}"}


async def _make_script(client, headers) -> str:
    res = await client.post(f"{API}/scripts", headers=headers, json={"title": "Scene 1"})
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["status"] == "draft" and body["source_kind"] == "manual"
    assert body["line_count"] == 0
    return body["id"]


async def test_script_crud_and_lines(client):
    headers = await _auth_headers(client)
    sid = await _make_script(client, headers)

    # add two lines; order_index auto-assigned
    a = await client.post(
        f"{API}/scripts/{sid}/lines",
        headers=headers,
        json={
            "text": "Hello.",
            "character_name_raw": "Aria",
            "style": "cheerful",
            "speech_rate": 1.1,
        },
    )
    b = await client.post(f"{API}/scripts/{sid}/lines", headers=headers, json={"text": "Goodbye."})
    assert a.status_code == 201 and b.status_code == 201, a.text
    aid, bid = a.json()["id"], b.json()["id"]
    assert a.json()["order_index"] == 0 and b.json()["order_index"] == 1
    assert a.json()["speech_rate"] == 1.1

    listed = await client.get(f"{API}/scripts/{sid}/lines", headers=headers)
    assert [line["id"] for line in listed.json()] == [aid, bid]

    # reorder
    re = await client.post(
        f"{API}/scripts/{sid}/lines:reorder", headers=headers, json={"line_ids": [bid, aid]}
    )
    assert re.status_code == 200
    assert [line["id"] for line in re.json()] == [bid, aid]

    # update + delete
    up = await client.patch(
        f"{API}/scripts/{sid}/lines/{aid}", headers=headers, json={"text": "Hi there."}
    )
    assert up.status_code == 200 and up.json()["text"] == "Hi there."
    rm = await client.delete(f"{API}/scripts/{sid}/lines/{bid}", headers=headers)
    assert rm.status_code == 204

    got = await client.get(f"{API}/scripts/{sid}", headers=headers)
    assert got.json()["line_count"] == 1


async def test_script_duplicate_copies_lines(client):
    headers = await _auth_headers(client)
    sid = await _make_script(client, headers)
    await client.post(f"{API}/scripts/{sid}/lines", headers=headers, json={"text": "Line A"})

    dup = await client.post(f"{API}/scripts/{sid}:duplicate", headers=headers)
    assert dup.status_code == 200
    assert dup.json()["title"] == "Scene 1 (copy)"
    assert dup.json()["line_count"] == 1
    dup_lines = await client.get(f"{API}/scripts/{dup.json()['id']}/lines", headers=headers)
    assert dup_lines.json()[0]["text"] == "Line A"


async def test_script_validate_flags_issues(client):
    headers = await _auth_headers(client)
    sid = await _make_script(client, headers)
    await client.post(f"{API}/scripts/{sid}/lines", headers=headers, json={"text": "   "})
    await client.post(
        f"{API}/scripts/{sid}/lines",
        headers=headers,
        json={"text": "Timed.", "character_id": "c_x", "start_ms": 500, "end_ms": 100},
    )

    res = await client.get(f"{API}/scripts/{sid}:validate", headers=headers)
    assert res.status_code == 200
    codes = {i["code"] for i in res.json()["issues"]}
    assert "empty_text" in codes and "no_speaker" in codes and "bad_timing" in codes


async def test_line_preview_synthesizes_with_speaker(client):
    headers = await _auth_headers(client)
    char = await client.post(f"{API}/characters", headers=headers, json={"name": "Aria"})
    cid = char.json()["id"]
    sid = await _make_script(client, headers)
    line = (
        await client.post(
            f"{API}/scripts/{sid}/lines",
            headers=headers,
            json={"text": "Hello there.", "character_id": cid, "style": "cheerful"},
        )
    ).json()

    res = await client.post(f"{API}/scripts/{sid}/lines/{line['id']}:preview", headers=headers)
    assert res.status_code == 200, res.text
    assert res.headers["content-type"] == "audio/wav"
    assert res.content[:4] == b"RIFF"


async def test_line_preview_requires_speaker(client):
    headers = await _auth_headers(client)
    sid = await _make_script(client, headers)
    line = (
        await client.post(f"{API}/scripts/{sid}/lines", headers=headers, json={"text": "Hi"})
    ).json()
    res = await client.post(f"{API}/scripts/{sid}/lines/{line['id']}:preview", headers=headers)
    assert res.status_code == 422, res.text


async def test_scripts_require_user(client):
    guest = await client.post(f"{API}/auth/guest")
    guest_headers = {"Authorization": f"Bearer {guest.json()['token']}"}
    res = await client.post(f"{API}/scripts", headers=guest_headers, json={"title": "Nope"})
    assert res.status_code == 403, res.text
