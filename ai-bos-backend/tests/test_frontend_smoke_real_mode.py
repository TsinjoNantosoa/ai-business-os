from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "demo1234"},
    )
    assert res.status_code == 200
    return res.json()["token"]


def test_platform_orgs_requires_auth() -> None:
    res = client.get("/api/v1/platform/organizations")
    assert res.status_code == 401


def test_platform_orgs_ok() -> None:
    token = login("ceo@demo.aibos.io")
    res = client.get("/api/v1/platform/organizations", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)
    assert body[0]["id"] == "org-1"


def test_dashboard_data_ok_for_staff() -> None:
    token = login("staff@demo.aibos.io")

    for path in [
        "/api/v1/finance/overview",
        "/api/v1/crm/leads",
        "/api/v1/crm/activities",
        "/api/v1/support/tickets",
        "/api/v1/hr/employees",
        "/api/v1/tasks",
        "/api/v1/projects",
        "/api/v1/calendar/events",
        "/api/v1/meetings",
    ]:
        res = client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, f"{path} => {res.status_code}"

