"""S34 — AI traces / usage summary observability."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _force_mock_llm(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", None)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    headers = {"Authorization": f"Bearer {login(email)}"}
    if settings.chatbot_api_token:
        headers["X-Chatbot-Token"] = settings.chatbot_api_token
    return headers


def test_chat_creates_trace_and_usage() -> None:
    headers = auth_headers()
    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "Bonjour, résumé KPIs", "agentId": None},
    ) as res:
        assert res.status_code == 200
        body = "".join(res.iter_text())
    assert "done" in body
    assert "traceId" in body

    traces = client.get("/api/v1/ai/traces", headers=auth_headers()).json()
    assert len(traces) >= 1
    latest = traces[0]
    assert latest["status"] in {"completed", "waiting_approval"}
    assert latest["inputTokens"] + latest["outputTokens"] >= 1

    summary = client.get("/api/v1/ai/usage/summary?days=30", headers=auth_headers()).json()
    assert summary["traceCount"] >= 1
    assert summary["totalTokens"] >= 1

    detail = client.get(f"/api/v1/ai/traces/{latest['id']}", headers=auth_headers()).json()
    assert detail["id"] == latest["id"]
    assert "llmCalls" in detail
    assert len(detail["llmCalls"]) >= 1


def test_usage_tenant_isolation() -> None:
    h1 = auth_headers("ceo@demo.aibos.io")
    h2 = auth_headers("ceo@eu.aibos.io")
    s1 = client.get("/api/v1/ai/usage/summary", headers=h1).json()
    s2 = client.get("/api/v1/ai/usage/summary", headers=h2).json()
    assert "totalCostUsd" in s1 and "totalCostUsd" in s2
