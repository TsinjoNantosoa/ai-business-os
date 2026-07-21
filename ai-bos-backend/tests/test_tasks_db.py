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


def test_tasks_list_from_db() -> None:
    res = client.get("/api/v1/tasks", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 20
    assert body[0]["status"] in {"todo", "in_progress", "review", "done"}


def test_task_status_update() -> None:
    headers = auth_headers()
    tasks = client.get("/api/v1/tasks", headers=headers).json()
    task_id = tasks[0]["id"]
    res = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        headers=headers,
        json={"status": "done"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "done"


def test_task_assign() -> None:
    headers = auth_headers()
    tasks = client.get("/api/v1/tasks", headers=headers).json()
    task_id = tasks[1]["id"]
    res = client.patch(
        f"/api/v1/tasks/{task_id}/assign",
        headers=headers,
        json={"assigneeId": "u-staff-1"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["assigneeId"] == "u-staff-1"
    assert body["assigneeName"] == "Lucas Thomas"


def test_task_create() -> None:
    headers = auth_headers()
    res = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={
            "title": "Phase4 task",
            "description": "Created by test",
            "priority": "high",
            "dueDate": "2026-08-01T00:00:00Z",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "Phase4 task"
    assert body["status"] == "todo"
    assert body["priority"] == "high"
    assert body["assigneeId"]
