from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_success() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@demo.aibos.io", "password": "demo1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["refreshToken"]
    assert body["user"]["email"] == "ceo@demo.aibos.io"


def test_refresh_success() -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@demo.aibos.io", "password": "demo1234"},
    )
    refresh_token = login.json()["refreshToken"]
    response = client.post("/api/v1/auth/refresh", json={"refreshToken": refresh_token})
    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["refreshToken"] != refresh_token


def test_refresh_survives_session_store_recreation() -> None:
    """Persistent refresh sessions remain valid when the service object restarts."""
    from app.main import auth_service
    from app.services.session_store import DatabaseRefreshSessionStore

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@demo.aibos.io", "password": "demo1234"},
    )
    refresh_token = login.json()["refreshToken"]
    auth_service._sessions = DatabaseRefreshSessionStore()
    response = client.post("/api/v1/auth/refresh", json={"refreshToken": refresh_token})
    assert response.status_code == 200
    assert response.json()["token"]


def test_refresh_rotation_reuse_and_logout() -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@demo.aibos.io", "password": "demo1234"},
    )
    first = login.json()["refreshToken"]
    rotated = client.post("/api/v1/auth/refresh", json={"refreshToken": first})
    assert rotated.status_code == 200
    second = rotated.json()["refreshToken"]
    assert client.post("/api/v1/auth/refresh", json={"refreshToken": first}).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refreshToken": second}).status_code == 401

    fresh = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@demo.aibos.io", "password": "demo1234"},
    ).json()
    assert client.post("/api/v1/auth/logout", json={"refreshToken": fresh["refreshToken"]}).status_code == 204
    assert client.post("/api/v1/auth/refresh", json={"refreshToken": fresh["refreshToken"]}).status_code == 401


def test_me_requires_bearer() -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_success() -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "staff@demo.aibos.io", "password": "demo1234"},
    )
    token = login.json()["token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "staff@demo.aibos.io"
    assert body["role"] == "staff"


def test_update_profile_and_password() -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "staff@demo.aibos.io", "password": "demo1234"},
    )
    assert login.status_code == 200
    token = login.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    patched = client.patch(
        "/api/v1/auth/me",
        headers=headers,
        json={"firstName": "Lucas", "lastName": "Thomas"},
    )
    assert patched.status_code == 200
    assert patched.json()["firstName"] == "Lucas"

    bad = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"currentPassword": "wrong", "newPassword": "newpass99"},
    )
    assert bad.status_code == 400

    changed = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"currentPassword": "demo1234", "newPassword": "newpass99"},
    )
    assert changed.status_code == 200

    relogin = client.post(
        "/api/v1/auth/login",
        json={"email": "staff@demo.aibos.io", "password": "newpass99"},
    )
    assert relogin.status_code == 200
    new_headers = {"Authorization": f"Bearer {relogin.json()['token']}"}

    restore = client.post(
        "/api/v1/auth/change-password",
        headers=new_headers,
        json={"currentPassword": "newpass99", "newPassword": "demo1234"},
    )
    assert restore.status_code == 200
