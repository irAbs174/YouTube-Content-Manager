"""Video streaming + thumbnails — Range semantics the <video> tag relies on."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import make_client, wait_for_render


def _rendered_client(settings):
    client_cm = make_client(settings)
    client = client_cm.__enter__()
    try:
        created = client.post(
            "/api/content",
            json={
                "title": "stream me",
                "date": _today(),
                "collection": "OSINT",
                "durationSec": 30,
                "render": True,
                "command": "whois example.com",
                "tip": "",
                "audio": True,
            },
        ).json()
        wait_for_render(client, created["id"])
        return client_cm, client, created["id"]
    except Exception:
        client_cm.__exit__(None, None, None)
        raise


def _today() -> str:
    from datetime import date

    return date.today().isoformat()


def test_thumbnail_served_after_render(settings):
    client_cm, client, episode_id = _rendered_client(settings)
    try:
        response = client.get(f"/api/content/{episode_id}/thumbnail")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert response.content
    finally:
        client_cm.__exit__(None, None, None)


def test_thumbnail_404_before_render(client: TestClient):
    row = client.get("/api/dashboard").json()["rows"][0]
    response = client.get(f"/api/content/{row['id']}/thumbnail")
    assert response.status_code == 404


def test_full_file_stream(settings):
    client_cm, client, episode_id = _rendered_client(settings)
    try:
        response = client.get(f"/api/content/{episode_id}/video")
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
        assert response.headers["accept-ranges"] == "bytes"
        assert int(response.headers["content-length"]) == len(response.content)
    finally:
        client_cm.__exit__(None, None, None)


def test_range_request_returns_206(settings):
    client_cm, client, episode_id = _rendered_client(settings)
    try:
        size = int(client.get(f"/api/content/{episode_id}/video").headers["content-length"])
        response = client.get(
            f"/api/content/{episode_id}/video", headers={"Range": "bytes=0-99"}
        )
        assert response.status_code == 206
        assert response.headers["content-range"] == f"bytes 0-99/{size}"
        assert len(response.content) == 100

        # open-ended range
        response = client.get(
            f"/api/content/{episode_id}/video", headers={"Range": "bytes=100-"}
        )
        assert response.status_code == 206
        assert len(response.content) == size - 100

        # suffix range: last 10 bytes
        response = client.get(
            f"/api/content/{episode_id}/video", headers={"Range": "bytes=-10"}
        )
        assert response.status_code == 206
        assert len(response.content) == 10
    finally:
        client_cm.__exit__(None, None, None)


def test_unsatisfiable_range_returns_416(settings):
    client_cm, client, episode_id = _rendered_client(settings)
    try:
        response = client.get(
            f"/api/content/{episode_id}/video",
            headers={"Range": "bytes=999999999-"},
        )
        assert response.status_code == 416
        assert response.headers["content-range"].startswith("bytes */")
    finally:
        client_cm.__exit__(None, None, None)


def test_download_header(settings):
    client_cm, client, episode_id = _rendered_client(settings)
    try:
        response = client.get(f"/api/content/{episode_id}/video?download=1")
        assert response.status_code == 200
        assert (
            response.headers["content-disposition"]
            == f'attachment; filename="episode-{episode_id}.mp4"'
        )
    finally:
        client_cm.__exit__(None, None, None)


def test_video_404_before_render(client: TestClient):
    row = client.get("/api/dashboard").json()["rows"][0]
    assert client.get(f"/api/content/{row['id']}/video").status_code == 404


def test_video_404_for_unknown_id(client: TestClient):
    assert client.get("/api/content/999999/video").status_code == 404
    assert client.get("/api/content/999999/thumbnail").status_code == 404
