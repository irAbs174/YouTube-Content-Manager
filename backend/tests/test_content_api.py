"""POST/PATCH/DELETE /api/content — validation + happy paths."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from tests.conftest import FakeRenderer, make_client, wait_for_render

VALID = {
    "title": "netcat listener on 9999",
    "date": date.today().isoformat(),
    "status": "Draft",
    "collection": "Network Hacking",
    "soundMusic": "Dark Modem",
    "effects": "Neon glow",
    "subtitles": "EN",
    "thumbnail": "thumbs/network-hacking/ep-99.jpg",
    "durationSec": 45,
    "render": False,
    "command": "",
    "tip": "",
    "audio": True,
}


def test_create_returns_camel_case_row(client: TestClient):
    response = client.post("/api/content", json=VALID)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == VALID["title"]
    assert body["collection"] == VALID["collection"]
    assert body["durationSec"] == 45
    assert body["renderStatus"] == "none"
    assert isinstance(body["episode"], int)
    # seeded dataset has 26 episodes → next is 27
    assert body["episode"] == 27


def test_create_is_slash_tolerant(client: TestClient):
    assert client.post("/api/content/", json=VALID).status_code == 201


def test_create_with_render_queues_job(settings):
    with make_client(settings) as client:
        payload = {**VALID, "render": True, "command": "nc -lv 9999"}
        response = client.post("/api/content", json=payload)
        assert response.status_code == 201
        body = response.json()
        assert body["renderStatus"] == "queued"
        state = wait_for_render(client, body["id"])
        assert state["renderStatus"] == "done"
        assert state["hasVideo"] is True


def test_create_render_without_command_is_400(client: TestClient):
    payload = {**VALID, "render": True, "command": "   "}
    response = client.post("/api/content", json=payload)
    assert response.status_code == 400
    assert "command" in response.json()["error"].lower()


def test_create_render_when_ffmpeg_missing_is_503(settings):
    with make_client(settings, renderer=FakeRenderer(available=False)) as client:
        payload = {**VALID, "render": True, "command": "nc -lv 9999"}
        response = client.post("/api/content", json=payload)
        assert response.status_code == 503
        assert "Uncheck" in response.json()["error"]


def test_create_without_render_saves_even_when_ffmpeg_missing(settings):
    with make_client(settings, renderer=FakeRenderer(available=False)) as client:
        response = client.post("/api/content", json=VALID)
        assert response.status_code == 201


def test_create_requires_title_length(client: TestClient):
    assert client.post("/api/content", json={**VALID, "title": "ab"}).status_code == 400
    assert (
        client.post("/api/content", json={**VALID, "title": "x" * 141}).status_code
        == 400
    )


def test_create_rejects_unknown_enums(client: TestClient):
    assert (
        client.post("/api/content", json={**VALID, "status": "Bogus"}).status_code == 400
    )
    assert (
        client.post("/api/content", json={**VALID, "collection": "Nope"}).status_code
        == 400
    )
    assert (
        client.post("/api/content", json={**VALID, "subtitles": "Klingon"}).status_code
        == 400
    )


def test_create_rejects_bad_duration_and_date(client: TestClient):
    assert (
        client.post("/api/content", json={**VALID, "durationSec": 2}).status_code == 400
    )
    assert (
        client.post("/api/content", json={**VALID, "durationSec": 999}).status_code == 400
    )
    assert (
        client.post("/api/content", json={**VALID, "date": "2026-13-01"}).status_code
        == 400
    )


def test_create_rejects_far_future_date(client: TestClient):
    response = client.post("/api/content", json={**VALID, "date": "2035-01-01"})
    assert response.status_code == 400


def test_patch_status_and_title(client: TestClient):
    created = client.post("/api/content", json=VALID).json()

    patched = client.patch(f"/api/content/{created['id']}", json={"status": "Published"})
    assert patched.status_code == 200
    assert patched.json() == {"ok": True, "id": created["id"]}

    dashboard = client.get("/api/dashboard").json()
    row = next(r for r in dashboard["rows"] if r["id"] == created["id"])
    assert row["status"] == "Published"

    renamed = client.patch(
        f"/api/content/{created['id']}", json={"title": "renamed episode"
    })
    assert renamed.status_code == 200
    dashboard = client.get("/api/dashboard").json()
    row = next(r for r in dashboard["rows"] if r["id"] == created["id"])
    assert row["title"] == "renamed episode"


def test_patch_rejects_unknown_status(client: TestClient):
    created = client.post("/api/content", json=VALID).json()
    response = client.patch(
        f"/api/content/{created['id']}", json={"status": "Bogus"}
    )
    assert response.status_code == 400


def test_patch_missing_episode_is_404(client: TestClient):
    assert client.patch("/api/content/99999", json={"status": "Draft"}).status_code == 404


def test_delete_removes_episode_and_stats(client: TestClient):
    created = client.post("/api/content", json=VALID).json()
    response = client.delete(f"/api/content/{created['id']}")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "id": created["id"]}
    assert client.delete(f"/api/content/{created['id']}").status_code == 404
    # gone from the dashboard
    dashboard = client.get("/api/dashboard").json()
    assert all(r["id"] != created["id"] for r in dashboard["rows"])


def test_delete_missing_is_404(client: TestClient):
    assert client.delete("/api/content/424242").status_code == 404


def test_invalid_json_body_is_400(client: TestClient):
    response = client.post(
        "/api/content", content=b"not json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400
    assert "error" in response.json()
