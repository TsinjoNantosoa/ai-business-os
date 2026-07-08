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


def test_projects_requires_auth() -> None:
    res = client.get("/api/v1/projects")
    assert res.status_code == 401


def test_projects_ok() -> None:
    token = login("ceo@demo.aibos.io")
    res = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body and body[0]["taskCount"] is not None


def test_calendar_events_ok() -> None:
    token = login("ceo@demo.aibos.io")
    res = client.get("/api/v1/calendar/events", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body and body[0]["type"]


def test_meetings_ok() -> None:
    token = login("ceo@demo.aibos.io")
    res = client.get("/api/v1/meetings", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body and body[0]["agenda"]

