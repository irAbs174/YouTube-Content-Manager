"""Login and session-cookie lifecycle tests."""

from fastapi.testclient import TestClient


def test_login_sets_cookie_and_authenticates_seeded_user(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@ytcm.test", "password": "demo-password-1"},
    )

    assert response.status_code == 200
    assert response.json() == {"id": 1, "email": "demo@ytcm.test"}
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("ytcm_session=")
    assert "httponly" in cookie.lower()
    assert "samesite=lax" in cookie.lower()

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json() == response.json()

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert logout.json() == {"ok": True}
    assert client.get("/api/auth/me").status_code == 401


def test_login_rejects_invalid_credentials_without_issuing_cookie(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@ytcm.test", "password": "not-the-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"error": "Invalid email or password"}
    assert "set-cookie" not in response.headers
