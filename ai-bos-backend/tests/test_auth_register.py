from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_creates_org_owner_and_returns_tokens() -> None:
    email = "founder.register@example.com"
    res = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "secure123",
            "firstName": "Ada",
            "lastName": "Lovelace",
            "organizationName": "Analytical Engines SAS",
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["token"]
    assert body["refreshToken"]
    assert body["user"]["email"] == email
    assert body["user"]["role"] == "owner"
    assert body["user"]["orgId"].startswith("org-")

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == email

    login = client.post("/api/v1/auth/login", json={"email": email, "password": "secure123"})
    assert login.status_code == 200


def test_register_rejects_duplicate_email() -> None:
    payload = {
        "email": "dup.register@example.com",
        "password": "secure123",
        "firstName": "Dup",
        "lastName": "User",
        "organizationName": "Dup Org",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    again = client.post("/api/v1/auth/register", json=payload)
    assert again.status_code == 409
