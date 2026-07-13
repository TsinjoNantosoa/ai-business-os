from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_oauth_providers_mock_mode() -> None:
    res = client.get("/api/v1/auth/oauth/providers")
    assert res.status_code == 200
    items = {p["id"]: p for p in res.json()["items"]}
    assert items["google"]["mode"] == "mock"
    assert items["microsoft"]["mode"] == "mock"


def test_oauth_mock_login_flow() -> None:
    start = client.get("/api/v1/auth/oauth/google/authorize")
    assert start.status_code == 200
    body = start.json()
    assert body["mode"] == "mock"
    assert body["state"]

    login_res = client.post(
        "/api/v1/auth/oauth/google/mock-login",
        json={"state": body["state"], "email": "ceo@demo.aibos.io"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert data["token"]
    assert data["user"]["email"] == "ceo@demo.aibos.io"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {data['token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ceo@demo.aibos.io"


def test_oauth_mock_creates_new_user() -> None:
    start = client.get("/api/v1/auth/oauth/microsoft/authorize")
    state = start.json()["state"]
    email = "oauth.new.user@example.com"
    res = client.post(
        "/api/v1/auth/oauth/microsoft/mock-login",
        json={"state": state, "email": email},
    )
    assert res.status_code == 200
    assert res.json()["user"]["email"] == email
    assert res.json()["user"]["role"] == "staff"


def test_oauth_invalid_state() -> None:
    res = client.post(
        "/api/v1/auth/oauth/google/mock-login",
        json={"state": "invalid-state-value-xx", "email": "ceo@demo.aibos.io"},
    )
    assert res.status_code == 400


def test_gdpr_export() -> None:
    res = client.get("/api/v1/platform/gdpr/export", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["exportVersion"] == "1.0"
    assert body["organization"]["id"] == "org-1"
    assert body["user"]["email"] == "ceo@demo.aibos.io"
    assert isinstance(body["contacts"], list)
    assert "tasks" in body


def test_gdpr_erase_staff() -> None:
    import secrets

    email = f"erase.{secrets.token_hex(4)}@example.com"
    start = client.get("/api/v1/auth/oauth/google/authorize").json()
    created = client.post(
        "/api/v1/auth/oauth/google/mock-login",
        json={"state": start["state"], "email": email},
    )
    assert created.status_code == 200, created.text
    token = created.json()["token"]
    assert created.json()["user"]["role"] == "staff"

    erase = client.post(
        "/api/v1/platform/gdpr/erase-request",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert erase.status_code == 200, erase.text
    assert erase.json()["active"] is False

    again_start = client.get("/api/v1/auth/oauth/google/authorize").json()
    again = client.post(
        "/api/v1/auth/oauth/google/mock-login",
        json={"state": again_start["state"], "email": email},
    )
    assert again.status_code == 403


def test_gdpr_erase_blocks_last_owner() -> None:
    res = client.post("/api/v1/platform/gdpr/erase-request", headers=auth_headers())
    assert res.status_code == 400
