from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _headers() -> dict[str, str]:
    login = client.post("/api/v1/auth/login", json={"email": "ceo@demo.aibos.io", "password": "demo1234"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_execution_history_contains_durable_steps() -> None:
    headers = _headers()
    workflows = client.get("/api/v1/workflows", headers=headers).json()
    active = next(item for item in workflows if item["status"] == "active")
    run = client.post(f"/api/v1/workflows/{active['id']}/run", headers=headers)
    assert run.status_code == 200
    history = client.get("/api/v1/workflows/executions", headers=headers).json()
    execution = next(item for item in history if item["id"] == run.json()["execution"]["id"])
    assert execution["steps"]
    for step in execution["steps"]:
        assert step["idempotencyKey"]
        assert step["attempts"] >= 1
        assert step["durationMs"] >= 1
        assert step["status"] in {"success", "error"}

