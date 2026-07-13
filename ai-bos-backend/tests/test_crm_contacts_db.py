from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.repositories.contact_repository import ContactRepository

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "demo1234"},
    )
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token or login()}"}


def test_contacts_loaded_from_database() -> None:
    with SessionLocal() as session:
        assert ContactRepository(session).count_by_org("org-1") >= 20

    res = client.get("/api/v1/crm/contacts", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 20
    assert body[0]["firstName"]
    assert body[0]["company"]


def test_contact_crud() -> None:
    headers = auth_headers()

    created = client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={
            "firstName": "Test",
            "lastName": "Contact",
            "email": "test.contact@example.com",
            "company": "Test Co",
            "phone": "+33 6 00 00 00 99",
            "position": "QA",
            "tags": ["test"],
        },
    )
    assert created.status_code == 201
    contact = created.json()
    contact_id = contact["id"]
    assert contact["email"] == "test.contact@example.com"

    updated = client.patch(
        f"/api/v1/crm/contacts/{contact_id}",
        headers=headers,
        json={"status": "lead", "company": "Test Co Updated"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "lead"
    assert updated.json()["company"] == "Test Co Updated"

    deleted = client.delete(f"/api/v1/crm/contacts/{contact_id}", headers=headers)
    assert deleted.status_code == 204

    missing = client.get("/api/v1/crm/contacts", headers=headers).json()
    assert all(item["id"] != contact_id for item in missing)


def test_staff_can_read_but_not_write_contacts() -> None:
    token = login("staff@demo.aibos.io")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/crm/contacts", headers=headers).status_code == 200
    assert client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={
            "firstName": "Nope",
            "lastName": "Write",
            "email": "nope@example.com",
            "company": "X",
        },
    ).status_code == 403
