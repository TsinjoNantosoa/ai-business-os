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
