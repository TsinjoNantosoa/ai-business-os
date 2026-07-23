"""S36 — agent client documentation endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_agent_docs_catalog() -> None:
    res = client.get("/api/v1/ai/docs", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["title"]
    assert len(body["tools"]) >= 5
    assert any(t["requiresApproval"] for t in body["tools"])
    assert len(body["workflowTemplates"]) >= 3
    assert "chat" in body["api"]


def test_agent_docs_guide_markdown() -> None:
    res = client.get("/api/v1/ai/docs/guide", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["format"] == "markdown"
    assert "Copilot" in body["content"]
    assert "HITL" in body["content"] or "approbation" in body["content"].lower()


def test_workflow_templates() -> None:
    res = client.get("/api/v1/workflows/templates", headers=auth_headers())
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 3
    assert items[0]["trigger"]
    assert items[0]["actions"]
