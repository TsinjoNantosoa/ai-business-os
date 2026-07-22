"""Lot B: write endpoints for sales orders, campaigns, projects, events, meetings."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_create_and_update_sales_order() -> None:
    h = headers()
    created = client.post(
        "/api/v1/sales/orders",
        headers=h,
        json={
            "customerName": "Client Test SARL",
            "lineItems": [
                {"description": "Pack CRM", "quantity": 2, "unitPrice": 1500},
                {"description": "Formation", "quantity": 1, "unitPrice": 800},
            ],
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["orderNumber"].startswith("SO-")
    assert body["amount"] == 3800
    assert body["status"] == "draft"
    assert len(body["lineItems"]) == 2

    updated = client.patch(
        f"/api/v1/sales/orders/{body['id']}",
        headers=h,
        json={"status": "sent"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "sent"

    listed = client.get("/api/v1/sales/orders", headers=h)
    assert any(o["id"] == body["id"] for o in listed.json())


def test_create_and_update_campaign() -> None:
    h = headers()
    created = client.post(
        "/api/v1/marketing/campaigns",
        headers=h,
        json={"name": "Campagne Test Q4", "type": "email", "budget": 5000},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["name"] == "Campagne Test Q4"
    assert body["status"] == "draft"

    updated = client.patch(
        f"/api/v1/marketing/campaigns/{body['id']}",
        headers=h,
        json={"status": "active", "budget": 7500},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "active"
    assert updated.json()["budget"] == 7500

    invalid = client.post(
        "/api/v1/marketing/campaigns",
        headers=h,
        json={"name": "Bad", "type": "tv"},
    )
    assert invalid.status_code == 400


def test_create_and_update_project() -> None:
    h = headers()
    created = client.post(
        "/api/v1/projects",
        headers=h,
        json={"name": "Projet Test Lot B", "description": "Desc", "budget": 10000},
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "planning"
    assert body["progress"] == 0
    assert body["teamMembers"], "creator should be a team member"

    updated = client.patch(
        f"/api/v1/projects/{body['id']}",
        headers=h,
        json={"status": "active", "progress": 25},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "active"
    assert updated.json()["progress"] == 25


def test_create_and_update_calendar_event() -> None:
    h = headers()
    created = client.post(
        "/api/v1/calendar/events",
        headers=h,
        json={
            "title": "Réunion test",
            "type": "meeting",
            "startDate": "2026-08-01T10:00:00Z",
            "endDate": "2026-08-01T11:00:00Z",
            "location": "Zoom",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()

    updated = client.patch(
        f"/api/v1/calendar/events/{body['id']}",
        headers=h,
        json={"title": "Réunion test décalée", "startDate": "2026-08-02T10:00:00Z"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Réunion test décalée"


def test_create_and_update_meeting() -> None:
    h = headers()
    created = client.post(
        "/api/v1/meetings",
        headers=h,
        json={
            "title": "Sync test",
            "date": "2026-08-05",
            "duration": 45,
            "agenda": ["Point 1", "Point 2"],
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "upcoming"
    assert body["attendees"], "creator should attend"

    updated = client.patch(
        f"/api/v1/meetings/{body['id']}",
        headers=h,
        json={"status": "completed", "summary": "Fait."},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"
    assert updated.json()["summary"] == "Fait."


def test_tenant_isolation_on_ops_resources() -> None:
    h1 = headers("ceo@demo.aibos.io")
    h2 = headers("ceo@eu.aibos.io")

    created = client.post(
        "/api/v1/projects",
        headers=h1,
        json={"name": "Projet privé org-1"},
    )
    assert created.status_code == 201
    project_id = created.json()["id"]

    # org-2 should not see or edit org-1's project
    listed = client.get("/api/v1/projects", headers=h2)
    assert all(p["id"] != project_id for p in listed.json())

    forbidden = client.patch(
        f"/api/v1/projects/{project_id}",
        headers=h2,
        json={"status": "active"},
    )
    assert forbidden.status_code == 404


def test_write_requires_permission() -> None:
    # staff has no sales.order.write / marketing.campaign.write
    h = headers("staff@demo.aibos.io")
    denied_order = client.post(
        "/api/v1/sales/orders",
        headers=h,
        json={"customerName": "X", "lineItems": [{"description": "d", "quantity": 1, "unitPrice": 1}]},
    )
    assert denied_order.status_code == 403

    denied_campaign = client.post(
        "/api/v1/marketing/campaigns",
        headers=h,
        json={"name": "X"},
    )
    assert denied_campaign.status_code == 403
