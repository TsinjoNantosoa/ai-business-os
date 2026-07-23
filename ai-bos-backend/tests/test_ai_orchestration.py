"""Lot D: multi-step orchestration + HITL approvals."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.repositories.task_repository import TaskRepository
from app.services.tool_registry import list_tools, plan_mock_tool_calls

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


def _sse_events(response) -> list[dict]:
    return [json.loads(line[6:]) for line in response.iter_lines() if line.startswith("data: ")]


def test_mutating_tools_require_approval_flag() -> None:
    by_name = {t.name: t for t in list_tools()}
    assert by_name["tasks_create"].requires_approval is True
    assert by_name["crm_create_lead"].requires_approval is True
    assert by_name["crm_search_contacts"].requires_approval is False


def test_mock_planner_multi_intent() -> None:
    planned = plan_mock_tool_calls("montre-moi les contacts et les factures en retard")
    names = {c.name for c in planned}
    assert "crm_search_contacts" in names
    assert "finance_list_invoices" in names


def test_chat_multi_step_emits_step_and_multiple_tools() -> None:
    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=auth_headers(),
        json={"message": "montre contacts et factures", "agentId": "ceo"},
    ) as response:
        assert response.status_code == 200
        events = _sse_events(response)

    types = [e.get("type") for e in events]
    assert "step" in types
    tool_names = [e.get("name") for e in events if e.get("type") == "tool_call"]
    assert "crm_search_contacts" in tool_names
    assert "finance_list_invoices" in tool_names
    assert "done" in types
    done = next(e for e in events if e["type"] == "done")
    assert done.get("status") == "completed"


def test_hitl_create_task_requires_approval_then_execute() -> None:
    before = 0
    db = SessionLocal()
    try:
        before = len(TaskRepository(db).list_by_org("org-1"))
    finally:
        db.close()

    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=auth_headers(),
        json={"message": "crée une tâche Relancer client VIP", "agentId": "ceo", "conversationId": "conv-hitl-1"},
    ) as response:
        assert response.status_code == 200
        events = _sse_events(response)

    approval = next(e for e in events if e.get("type") == "approval_required")
    assert approval["name"] == "tasks_create"
    assert approval["approvalId"]
    done = next(e for e in events if e.get("type") == "done")
    assert done.get("status") == "waiting_approval"
    assert not any(e.get("type") == "tool_result" and e.get("name") == "tasks_create" for e in events)

    decide = client.post(
        f"/api/v1/ai/approvals/{approval['approvalId']}/decide",
        headers=auth_headers(),
        json={"decision": "approve"},
    )
    assert decide.status_code == 200
    body = decide.json()
    assert body["status"] == "executed"
    assert body["toolName"] == "tasks_create"

    db = SessionLocal()
    try:
        after = len(TaskRepository(db).list_by_org("org-1"))
        assert after == before + 1
    finally:
        db.close()


def test_hitl_reject_does_not_mutate() -> None:
    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=auth_headers(),
        json={"message": "crée un lead chez Acme Corp", "agentId": "sales"},
    ) as response:
        events = _sse_events(response)
    approval = next(e for e in events if e.get("type") == "approval_required")
    assert approval["name"] == "crm_create_lead"

    decide = client.post(
        f"/api/v1/ai/approvals/{approval['approvalId']}/decide",
        headers=auth_headers(),
        json={"decision": "reject"},
    )
    assert decide.status_code == 200
    assert decide.json()["status"] == "rejected"


def test_list_pending_approvals() -> None:
    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=auth_headers(),
        json={"message": "crée une tâche Checklist HITL", "agentId": "ceo"},
    ) as response:
        events = _sse_events(response)
    approval_id = next(e["approvalId"] for e in events if e.get("type") == "approval_required")

    listed = client.get("/api/v1/ai/approvals?status=pending", headers=auth_headers())
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()["items"]}
    assert approval_id in ids
