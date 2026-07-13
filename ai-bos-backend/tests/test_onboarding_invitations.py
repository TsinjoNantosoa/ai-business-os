from __future__ import annotations

import secrets

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "demo1234"},
    )
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_get_my_organization() -> None:
    res = client.get("/api/v1/platform/organizations/me", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "org-1"
    assert body["name"] == "Acme Corp"
    assert body["currency"] == "EUR"


def test_update_organization_onboarding() -> None:
    headers = auth_headers()
    res = client.patch(
        "/api/v1/platform/organizations/me",
        headers=headers,
        json={
            "name": "Acme Corp Updated",
            "currency": "USD",
            "timezone": "America/New_York",
            "address": "1 Broadway, New York",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Acme Corp Updated"
    assert body["currency"] == "USD"
    assert body["address"] == "1 Broadway, New York"

    # restore demo defaults for other tests
    client.patch(
        "/api/v1/platform/organizations/me",
        headers=headers,
        json={
            "name": "Acme Corp",
            "currency": "EUR",
            "timezone": "Europe/Paris",
            "address": "123 rue de la Paix, 75001 Paris",
        },
    )


def test_list_team_members() -> None:
    res = client.get("/api/v1/platform/team", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 2
    emails = {m["email"] for m in body}
    assert "ceo@demo.aibos.io" in emails


def test_team_requires_permission() -> None:
    res = client.get("/api/v1/platform/team", headers=auth_headers("staff@demo.aibos.io"))
    assert res.status_code == 403


def test_invite_and_accept_flow() -> None:
    headers = auth_headers()
    unique_email = f"invitee.s9.{secrets.token_hex(4)}@example.com"
    create = client.post(
        "/api/v1/platform/invitations",
        headers=headers,
        json={"email": unique_email, "role": "staff", "message": "Join us"},
    )
    assert create.status_code == 201, create.text
    invitation = create.json()
    assert invitation["email"] == unique_email
    assert invitation["status"] == "pending"
    token = invitation["token"]
    assert token

    preview = client.get(f"/api/v1/platform/invitations/by-token/{token}")
    assert preview.status_code == 200
    assert preview.json()["organizationName"]

    accept = client.post(
        "/api/v1/platform/invitations/accept",
        json={
            "token": token,
            "firstName": "Invite",
            "lastName": "S9",
            "password": "welcome123",
        },
    )
    assert accept.status_code == 201
    user = accept.json()
    assert user["email"] == unique_email
    assert user["role"] == "staff"

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": "welcome123"},
    )
    assert login_res.status_code == 200

    # second accept should fail
    again = client.post(
        "/api/v1/platform/invitations/accept",
        json={
            "token": token,
            "firstName": "Invite",
            "lastName": "S9",
            "password": "welcome123",
        },
    )
    assert again.status_code == 410


def test_cannot_invite_existing_user() -> None:
    res = client.post(
        "/api/v1/platform/invitations",
        headers=auth_headers(),
        json={"email": "staff@demo.aibos.io", "role": "staff"},
    )
    assert res.status_code == 409


def test_seed_invitation_pending() -> None:
    res = client.get("/api/v1/platform/invitations", headers=auth_headers())
    assert res.status_code == 200
    emails = {inv["email"] for inv in res.json()}
    assert "nouveau@acme.com" in emails
