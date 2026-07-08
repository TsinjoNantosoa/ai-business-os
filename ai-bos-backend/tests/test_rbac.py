from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "demo1234"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_rbac_users_requires_auth() -> None:
    response = client.get("/api/v1/rbac/users")
    assert response.status_code == 401


def test_rbac_users_owner_ok() -> None:
    token = login("ceo@demo.aibos.io")
    response = client.get("/api/v1/rbac/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert any(u["id"] == "u-owner-1" for u in body["items"])


def test_rbac_users_staff_forbidden() -> None:
    token = login("staff@demo.aibos.io")
    response = client.get("/api/v1/rbac/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

