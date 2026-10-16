"""API contract tests — the JSON dialect the frontend depends on.

These fail loudly when someone renames a response key, so frontend and
backend cannot silently drift apart.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

DASHBOARD_KEYS = {"range", "kpis", "series", "rows", "generatedAt"}
KPI_KEYS = {"views", "watchHours", "subs", "ctr", "likes"}
KPI_PAIR_KEYS = {"value", "prev"}
SERIES_KEYS = {"day", "views", "watchHours", "subs", "ctr", "likes"}
ROW_KEYS = {
    "id",
    "episode",
    "date",
    "title",
    "status",
    "collection",
    "soundMusic",
    "effects",
    "subtitles",
    "thumbnail",
    "durationSec",
    "script",
    "renderStatus",
    "renderProgress",
    "renderError",
    "videoPath",
    "hasVideo",
    "views",
    "impressions",
    "likes",
    "subs",
}
RENDER_KEYS = {"id", "renderStatus", "renderProgress", "renderError", "hasVideo"}


def test_dashboard_contract(client: TestClient):
    body = client.get("/api/dashboard").json()
    assert set(body) == DASHBOARD_KEYS
    assert set(body["kpis"]) == KPI_KEYS
    for pair in body["kpis"].values():
        assert set(pair) == KPI_PAIR_KEYS
    for point in body["series"]:
        assert set(point) == SERIES_KEYS
    for row in body["rows"]:
        # legacy keys must still be present; new keys are additive
        assert set(row) >= ROW_KEYS
        # also check new workbook keys present
        for k in ("visibility", "seriesName", "episodeNumber", "soundEffects", "music", "subtitlesCount", "thumbnailReady"):
            assert k in row


def test_render_state_contract(client: TestClient):
    row = client.get("/api/dashboard").json()["rows"][0]
    body = client.get(f"/api/renders?ids={row['id']}").json()
    assert len(body) == 1
    assert set(body[0]) == RENDER_KEYS


def test_mutation_contract(client: TestClient):
    created = client.post(
        "/api/content",
        json={
            "title": "contract probe",
            "date": _today(),
            "collection": "OSINT",
            "render": False,
        },
    ).json()
    assert set(created) | {"videoPath"} >= {
        "id",
        "episode",
        "renderStatus",
        "soundMusic",
        "durationSec",
    }

    patched = client.patch(
        f"/api/content/{created['id']}", json={"status": "Public"}
    ).json()
    assert patched == {"ok": True, "id": created["id"]}


def test_dashboard_meta_endpoint_lists_domain_values(client: TestClient):
    """The constants endpoint keeps frontend dropdowns in sync."""
    meta = client.get("/api/meta").json()
    assert meta["statuses"][0] == "Private"
    assert meta["collections"][0]["name"]
    assert all("color" in c and "sounds" in c for c in meta["collections"])


def _today() -> str:
    from datetime import date

    return date.today().isoformat()
