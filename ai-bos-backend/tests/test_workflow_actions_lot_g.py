"""Lot G — workflow action executors (email, task, notify)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app, email_service
from app.services.email_service import EmailService

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_run_workflow_executes_real_actions() -> None:
    # Force log mode for predictable outbox during the test
    assert isinstance(email_service, EmailService)
    previous_mode = email_service.mode
    email_service.mode = "log"
    email_service.outbox.clear()

    headers = auth_headers()
    try:
        created = client.post(
            "/api/v1/workflows",
            headers=headers,
            json={
                "name": "Lot G actions",
                "status": "active",
                "definition": {
                    "nodes": [
                        {
                            "id": "t1",
                            "type": "trigger",
                            "position": {"x": 0, "y": 0},
                            "data": {"label": "Manuel", "kind": "trigger"},
                        },
                        {
                            "id": "a1",
                            "type": "action",
                            "position": {"x": 200, "y": 0},
                            "data": {"label": "Envoyer email", "kind": "action"},
                        },
                        {
                            "id": "a2",
                            "type": "action",
                            "position": {"x": 400, "y": 0},
                            "data": {"label": "Créer tâche", "kind": "action"},
                        },
                        {
                            "id": "a3",
                            "type": "action",
                            "position": {"x": 600, "y": 0},
                            "data": {"label": "Notifier Slack", "kind": "action"},
                        },
                    ],
                    "edges": [
                        {"id": "e1", "source": "t1", "target": "a1"},
                        {"id": "e2", "source": "a1", "target": "a2"},
                        {"id": "e3", "source": "a2", "target": "a3"},
                    ],
                },
            },
        ).json()

        run = client.post(f"/api/v1/workflows/{created['id']}/run", headers=headers)
        assert run.status_code == 200
        body = run.json()
        assert body["execution"]["status"] == "success"
        msg = body["execution"]["resultMessage"] or ""
        assert "Envoyer email[ok]" in msg
        assert "Créer tâche[ok]" in msg
        assert "Notifier Slack[ok]" in msg
        assert len(email_service.outbox) >= 1

        tasks = client.get("/api/v1/tasks", headers=headers).json()
        assert any("Lot G" in (t.get("title") or "") or "workflow" in (t.get("tags") or []) for t in tasks)
    finally:
        email_service.mode = previous_mode


def test_lead_event_runs_actions_and_updates_crm() -> None:
    headers = auth_headers()
    # Custom workflow with CRM update
    client.post(
        "/api/v1/workflows",
        headers=headers,
        json={
            "name": "Lead qualify Lot G",
            "status": "active",
            "definition": {
                "nodes": [
                    {
                        "id": "t1",
                        "type": "trigger",
                        "position": {"x": 0, "y": 0},
                        "data": {"label": "Lead créé", "kind": "trigger"},
                    },
                    {
                        "id": "a1",
                        "type": "action",
                        "position": {"x": 200, "y": 0},
                        "data": {"label": "Mettre à jour CRM", "kind": "action"},
                    },
                ],
                "edges": [{"id": "e1", "source": "t1", "target": "a1"}],
            },
        },
    )

    lead = client.post(
        "/api/v1/crm/leads",
        headers=headers,
        json={
            "title": "Qualify me",
            "company": "G Corp",
            "contactName": "Grace",
            "value": 9000,
            "expectedCloseDate": "2026-12-31T00:00:00Z",
        },
    ).json()

    leads = client.get("/api/v1/crm/leads", headers=headers).json()
    match = next(l for l in leads if l["id"] == lead["id"])
    assert match["stage"] == "qualified"
