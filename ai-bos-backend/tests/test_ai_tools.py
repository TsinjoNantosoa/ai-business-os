"""Lot C: AI tool registry + RBAC + SSE tool events."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.services.tool_registry import (
    ToolContext,
    execute_tool,
    list_tools,
    plan_mock_tool_calls,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def _force_mock_llm(monkeypatch):
    """Avoid calling real OpenAI during unit tests (even if .env has a key)."""
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


def test_registry_lists_mvp_tools() -> None:
    names = {tool.name for tool in list_tools()}
    assert {
        "crm_search_contacts",
        "crm_create_lead",
        "finance_list_invoices",
        "tasks_create",
        "projects_list",
    } <= names


def test_list_tools_endpoint() -> None:
    res = client.get("/api/v1/ai/tools", headers=auth_headers())
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 5
    assert all("permissions" in item and "parameters" in item for item in items)


def test_tool_refuses_without_permission() -> None:
    db = SessionLocal()
    try:
        ctx = ToolContext(
            db=db,
            org_id="org-1",
            user_id="u-staff-1",
            user_name="Lucas Thomas",
            permissions={"dashboard.read", "task.read"},  # no crm.lead.write
        )
        result = execute_tool(
            "crm_create_lead",
            {
                "title": "Lead interdit",
                "company": "Acme",
                "contactName": "Test",
                "value": 1000,
            },
            ctx,
        )
        assert result.ok is False
        assert result.error and "Permission" in result.error
    finally:
        db.close()


def test_owner_can_search_contacts_and_list_invoices() -> None:
    db = SessionLocal()
    try:
        ctx = ToolContext(
            db=db,
            org_id="org-1",
            user_id="u-owner-1",
            user_name="Jean Bernard",
            permissions={"crm.contact.read", "finance.invoice.read", "project.read"},
        )
        contacts = execute_tool("crm_search_contacts", {"limit": 5}, ctx)
        assert contacts.ok
        assert contacts.data["count"] >= 1

        invoices = execute_tool("finance_list_invoices", {"limit": 5}, ctx)
        assert invoices.ok
        assert "invoices" in invoices.data

        projects = execute_tool("projects_list", {"limit": 5}, ctx)
        assert projects.ok
        assert projects.data["count"] >= 1
    finally:
        db.close()


def test_mock_planner_detects_intents() -> None:
    assert plan_mock_tool_calls("montre-moi les contacts")[0].name == "crm_search_contacts"
    assert plan_mock_tool_calls("quelles factures sont en retard ?")[0].name == "finance_list_invoices"
    assert plan_mock_tool_calls("crée une tâche Relancer client")[0].name == "tasks_create"
    assert plan_mock_tool_calls("liste les projets")[0].name == "projects_list"


def test_chat_sse_emits_tool_events_for_contacts() -> None:
    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=auth_headers(),
        json={"message": "montre-moi les contacts CRM", "agentId": "sales", "context": "Copilot"},
    ) as response:
        assert response.status_code == 200
        events: list[dict] = []
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            events.append(json.loads(line[6:]))

    types = [e.get("type") for e in events]
    assert "tool_call" in types
    assert "tool_result" in types
    assert "done" in types

    tool_call = next(e for e in events if e["type"] == "tool_call")
    assert tool_call["name"] == "crm_search_contacts"
    tool_result = next(e for e in events if e["type"] == "tool_result")
    assert tool_result["ok"] is True
    assert tool_result["result"]["count"] >= 1


def test_chat_tool_create_task() -> None:
    with client.stream(
        "POST",
        "/api/v1/ai/chat",
        headers=auth_headers("ceo@demo.aibos.io"),
        json={"message": "crée une tâche Préparer démo Lot C", "agentId": "ceo"},
    ) as response:
        assert response.status_code == 200
        events = [json.loads(line[6:]) for line in response.iter_lines() if line.startswith("data: ")]
    assert any(e.get("type") == "tool_call" and e.get("name") == "tasks_create" for e in events)
    assert any(e.get("type") == "approval_required" and e.get("name") == "tasks_create" for e in events)
    assert any(e.get("type") == "done" and e.get("status") == "waiting_approval" for e in events)
