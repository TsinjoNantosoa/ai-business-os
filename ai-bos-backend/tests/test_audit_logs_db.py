from __future__ import annotations

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


def test_audit_logs_list_from_db() -> None:
    res = client.get("/api/v1/platform/audit-logs", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 30
    assert body[0]["action"]
    assert body[0]["resource"]
    assert body[0]["timestamp"]


def test_audit_logs_requires_permission() -> None:
    res = client.get("/api/v1/platform/audit-logs", headers=auth_headers("staff@demo.aibos.io"))
    assert res.status_code == 403


def test_mutation_writes_audit_log() -> None:
    headers = auth_headers()
    before = client.get("/api/v1/platform/audit-logs", headers=headers).json()
    before_count = len(before)

    create = client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={
            "firstName": "Audit",
            "lastName": "Test",
            "email": "audit.test@example.com",
            "company": "AuditCo",
        },
    )
    assert create.status_code == 201
    contact_id = create.json()["id"]

    after = client.get("/api/v1/platform/audit-logs", headers=headers).json()
    assert after[0]["action"] == "CREATE"
    assert after[0]["resource"] == "Contact"
    assert after[0]["resourceId"] == contact_id
    # Liste plafonnée (limit=100) : on vérifie l'entrée récente, pas seulement le count.
    assert any(e["resourceId"] == contact_id and e["action"] == "CREATE" for e in after)
