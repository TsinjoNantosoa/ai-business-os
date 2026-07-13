from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

DEMO_API_KEY = "aibos_sk_demo_integration_key_do_not_share"


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_list_api_keys() -> None:
    res = client.get("/api/v1/platform/api-keys", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 1
    assert body[0]["maskedKey"]
    assert "secret" not in body[0]


def test_create_and_revoke_api_key() -> None:
    headers = auth_headers()
    create = client.post(
        "/api/v1/platform/api-keys",
        headers=headers,
        json={"name": "CI Test Key", "scopes": ["crm.contact.read", "dashboard.read"]},
    )
    assert create.status_code == 201
    data = create.json()
    assert data["secret"].startswith("aibos_sk_")
    assert data["name"] == "CI Test Key"
    key_id = data["id"]
    secret = data["secret"]

    # Use the new key via X-Api-Key
    contacts = client.get("/api/v1/crm/contacts", headers={"X-Api-Key": secret})
    assert contacts.status_code == 200

    # Missing scope should 403
    forbidden = client.get("/api/v1/crm/leads", headers={"X-Api-Key": secret})
    assert forbidden.status_code == 403

    revoke = client.delete(f"/api/v1/platform/api-keys/{key_id}", headers=headers)
    assert revoke.status_code == 204

    dead = client.get("/api/v1/crm/contacts", headers={"X-Api-Key": secret})
    assert dead.status_code == 401


def test_demo_api_key_auth_bearer() -> None:
    res = client.get(
        "/api/v1/crm/contacts",
        headers={"Authorization": f"Bearer {DEMO_API_KEY}"},
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_keys_require_settings_org() -> None:
    res = client.get("/api/v1/platform/api-keys", headers=auth_headers("staff@demo.aibos.io"))
    assert res.status_code == 403


def test_invalid_api_key() -> None:
    res = client.get("/api/v1/crm/contacts", headers={"X-Api-Key": "aibos_sk_invalid_key_xxxxx"})
    assert res.status_code == 401
