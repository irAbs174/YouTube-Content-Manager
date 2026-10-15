"""GET /api/dashboard — filters, KPI math, series shape."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

TODAY = date.today()


def test_default_range_is_90_days(client: TestClient):
    body = client.get("/api/dashboard").json()
    assert body["range"]["days"] == 90
    assert body["range"]["from"] == (TODAY - timedelta(days=89)).isoformat()
    assert body["range"]["to"] == TODAY.isoformat()
    assert len(body["series"]) == 90
    assert body["generatedAt"]


def test_kpis_match_series_totals(client: TestClient):
    body = client.get("/api/dashboard").json()
    views = sum(point["views"] for point in body["series"])
    likes = sum(point["likes"] for point in body["series"])
    subs = sum(point["subs"] for point in body["series"])
    assert body["kpis"]["views"]["value"] == views
    assert body["kpis"]["likes"]["value"] == likes
    assert body["kpis"]["subs"]["value"] == subs
    # prior window is populated from the 180-day seed history
    assert body["kpis"]["views"]["prev"] > 0


def test_rows_carry_window_metrics(client: TestClient):
    body = client.get("/api/dashboard").json()
    assert body["rows"], "seeded episodes should appear"
    row = body["rows"][0]
    for key in ("views", "impressions", "likes", "subs", "hasVideo"):
        assert key in row
    assert row["views"] >= 0


def test_collection_filter(client: TestClient):
    body = client.get(
        "/api/dashboard",
        params={"collection": "Linux Basics"},
    ).json()
    assert body["rows"]
    assert {row["collection"] for row in body["rows"]} == {"Linux Basics"}


def test_status_filter(client: TestClient):
    body = client.get("/api/dashboard", params={"status": "Published"}).json()
    assert body["rows"]
    assert {row["status"] for row in body["rows"]} == {"Published"}


def test_date_window_filtering(client: TestClient):
    # A narrow 7-day window — episodes dated outside it must not appear.
    body = client.get(
        "/api/dashboard",
        params={"from": (TODAY - timedelta(days=6)).isoformat(), "to": TODAY.isoformat()},
    ).json()
    assert body["range"]["days"] == 7
    assert len(body["series"]) == 7
    earliest = (TODAY - timedelta(days=6)).isoformat()
    assert all(row["date"] >= earliest for row in body["rows"])


def test_from_after_to_is_400(client: TestClient):
    response = client.get(
        "/api/dashboard",
        params={"from": TODAY.isoformat(), "to": (TODAY - timedelta(days=3)).isoformat()},
    )
    assert response.status_code == 400


def test_invalid_date_is_400(client: TestClient):
    assert client.get("/api/dashboard", params={"from": "junk"}).status_code == 400


def test_unknown_collection_is_400(client: TestClient):
    assert (
        client.get("/api/dashboard", params={"collection": "Nope"}).status_code == 400
    )


def test_unknown_status_is_400(client: TestClient):
    assert client.get("/api/dashboard", params={"status": "Nope"}).status_code == 400


def test_range_over_two_years_is_400(client: TestClient):
    response = client.get(
        "/api/dashboard",
        params={"from": "2023-01-01", "to": TODAY.isoformat()},
    )
    assert response.status_code == 400
