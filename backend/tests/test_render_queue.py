"""Render-queue orchestration: enqueue → running → done/failed, retries."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import FakeRenderer, make_client, wait_for_render


def _create_with_render(client: TestClient, command: str = "nc -lv 9999") -> dict:
    response = client.post(
        "/api/content",
        json={
            "title": "render me",
            "date": _today(),
            "collection": "Network Hacking",
            "durationSec": 30,
            "render": True,
            "command": command,
            "tip": "listener confirmed",
            "audio": False,
        },
    )
    assert response.status_code == 201
    return response.json()


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


def test_full_render_lifecycle(settings):
    renderer = FakeRenderer()
    with make_client(settings, renderer=renderer) as client:
        created = _create_with_render(client)
        state = wait_for_render(client, created["id"])
        assert state["renderStatus"] == "done"
        assert state["renderProgress"] == 100
        assert state["hasVideo"] is True
        assert state["renderError"] is None
        assert renderer.rendered == [created["id"]]


def test_render_failure_sets_error_and_retry_works(settings):
    # failure is keyed by command so it is armed before the job is queued
    renderer = FakeRenderer(fail_commands={"trigger-boom": "encoder exploded"})
    with make_client(settings, renderer=renderer) as client:
        created = _create_with_render(client, command="trigger-boom")

        state = wait_for_render(client, created["id"], want="failed")
        assert state["renderStatus"] == "failed"
        assert "encoder exploded" in state["renderError"]

        # retry succeeds once the fault clears
        renderer.fail_commands.pop("trigger-boom")
        response = client.post(f"/api/content/{created['id']}/render")
        assert response.status_code == 202
        state = wait_for_render(client, created["id"])
        assert state["renderStatus"] == "done"


def test_reenqueue_while_running_returns_200(settings):
    with make_client(settings) as client:
        created = _create_with_render(client)
        # immediate re-request: job is queued/running → 200, not a second job
        response = client.post(f"/api/content/{created['id']}/render")
        assert response.status_code == 200
        wait_for_render(client, created["id"])


def test_enqueue_missing_episode_is_404(client: TestClient):
    assert client.post("/api/content/999999/render").status_code == 404


def test_enqueue_synthesises_script_for_legacy_rows(client: TestClient):
    """Seeded episodes have no script; the endpoint derives one from the title."""
    row = client.get("/api/dashboard").json()["rows"][0]
    response = client.post(f"/api/content/{row['id']}/render")
    assert response.status_code == 202
    state = wait_for_render(client, row["id"])
    assert state["renderStatus"] == "done"


def test_enqueue_reports_ffmpeg_unavailable(settings):
    renderer = FakeRenderer(available=False)
    with make_client(settings, renderer=renderer) as client:
        # saving without rendering works even when FFmpeg is missing…
        created = client.post(
            "/api/content",
            json={
                "title": "no ffmpeg here",
                "date": _today(),
                "collection": "OSINT",
                "durationSec": 30,
                "render": False,
            },
        )
        assert created.status_code == 201
        # …but the render endpoint reports 503 with a helpful message
        response = client.post(f"/api/content/{created.json()['id']}/render")
        assert response.status_code == 503
        assert "FFmpeg" in response.json()["error"]
