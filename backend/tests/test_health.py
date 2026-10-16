"""Health endpoint."""

from fastapi.testclient import TestClient


def test_health_ok(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
