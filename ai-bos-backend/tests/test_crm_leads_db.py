from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.repositories.activity_repository import ActivityRepository
from app.repositories.lead_repository import LeadRepository

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


def test_leads_loaded_from_database() -> None:
    with SessionLocal() as session:
        assert LeadRepository(session).count_all() >= 15

    res = client.get("/api/v1/crm/leads", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 15
    assert body[0]["title"]
    assert body[0]["probability"] >= 0


def test_activities_loaded_from_database() -> None:
    with SessionLocal() as session:
        assert ActivityRepository(session).count_all() >= 20

    res = client.get("/api/v1/crm/activities", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 20
    assert body[0]["type"] in {"call", "email", "meeting", "note", "task"}


def test_lead_stage_update() -> None:
    headers = auth_headers()
    leads = client.get("/api/v1/crm/leads", headers=headers).json()
    lead_id = leads[0]["id"]

    updated = client.patch(
        f"/api/v1/crm/leads/{lead_id}/stage",
        headers=headers,
        json={"stage": "negotiation"},
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["stage"] == "negotiation"
    assert body["probability"] == 75


def test_create_lead() -> None:
    headers = auth_headers()
    close_date = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    created = client.post(
        "/api/v1/crm/leads",
        headers=headers,
        json={
            "title": "Deal test",
            "company": "Test Corp",
            "contactName": "Alice Test",
            "value": 15000,
            "expectedCloseDate": close_date,
        },
    )
    assert created.status_code == 201
    assert created.json()["stage"] == "new"
