"""GET /api/renders — the lightweight polling endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_no_ids_returns_empty_list(client: TestClient):
    assert client.get("/api/renders").json() == []
    assert client.get("/api/renders?ids=").json() == []
    assert client.get("/api/renders?ids=abc,def").json() == []


def test_returns_requested_states_in_order(client: TestClient):
    dashboard = client.get("/api/dashboard").json()
    ids = [row["id"] for row in dashboard["rows"][:3]]
    body = client.get("/api/renders", params={"ids": ",".join(map(str, ids))}).json()
    assert [state["id"] for state in body] == ids
    for state in body:
        assert state["renderStatus"] in ("none", "queued", "running", "done", "failed")
        assert 0 <= state["renderProgress"] <= 100
        assert state["hasVideo"] is False  # nothing rendered yet


def test_unknown_ids_are_dropped(client: TestClient):
    body = client.get("/api/renders?ids=99998,99999").json()
    assert body == []


def test_mixed_known_and_unknown_ids(client: TestClient):
    row = client.get("/api/dashboard").json()["rows"][0]
    body = client.get(f"/api/renders?ids=99999,{row['id']}").json()
    assert [state["id"] for state in body] == [row["id"]]
