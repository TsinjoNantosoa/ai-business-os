from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.core.config import settings
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
    headers = {"Authorization": f"Bearer {login(email)}"}
    if settings.chatbot_api_token:
        headers["X-Chatbot-Token"] = settings.chatbot_api_token
    return headers


def test_ai_agents_requires_permission() -> None:
    res = client.get("/api/v1/ai/agents", headers={"Authorization": f"Bearer {login('staff@demo.aibos.io')}"})
    assert res.status_code == 403


def test_ai_agents_owner_ok() -> None:
    res = client.get("/api/v1/ai/agents", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 6
    assert body[0]["slug"] == "ceo"


def test_ai_chat_requires_chatbot_token_when_configured() -> None:
    if not settings.chatbot_api_token:
        return
    res = client.post(
        "/api/v1/ai/chat",
        headers={"Authorization": f"Bearer {login()}"},
        json={"message": "test"},
    )
    assert res.status_code == 403


def test_ai_chat_requires_auth() -> None:
    res = client.post("/api/v1/ai/chat", json={"message": "Bonjour"})
    assert res.status_code == 401


def test_ai_chat_streams_sse() -> None:
    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=auth_headers(),
        json={"message": "Quelles factures sont en retard ?", "agentId": "finance", "context": "Finance"},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        chunks: list[str] = []
        done = False
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = json.loads(line[6:])
            if payload.get("type") == "chunk":
                chunks.append(payload["content"])
            if payload.get("type") == "done":
                done = True
                assert payload.get("provider") in {"mock", "openai"}
        assert done
        assert "".join(chunks).strip()
