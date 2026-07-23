"""Lot F / S33 — event bus, inbound webhooks, CRM lead → workflow dispatch."""

from __future__ import annotations

import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_event_catalog() -> None:
    res = client.get("/api/v1/events/catalog", headers=auth_headers())
    assert res.status_code == 200
    types = {item["eventType"] for item in res.json()}
    assert "crm.lead.created" in types
    assert "webhook.inbound" in types


def test_lead_create_triggers_active_workflow() -> None:
    headers = auth_headers()
    before = client.get("/api/v1/workflows/executions", headers=headers).json()
    before_n = len(before)

    lead = client.post(
        "/api/v1/crm/leads",
        headers=headers,
        json={
            "title": "Lot F Lead",
            "company": "Acme Events",
            "contactName": "Ada Lovelace",
            "value": 5000,
            "currency": "EUR",
            "stage": "new",
            "expectedCloseDate": "2026-12-31T00:00:00Z",
        },
    )
    assert lead.status_code == 201

    events = client.get("/api/v1/events", headers=headers).json()
    assert any(e["eventType"] == "crm.lead.created" for e in events)
    lead_events = [e for e in events if e["eventType"] == "crm.lead.created"]
    assert lead_events[0]["triggeredWorkflowIds"]

    after = client.get("/api/v1/workflows/executions", headers=headers).json()
    assert len(after) > before_n
    latest = after[0]
    assert latest["triggerSource"] in {"crm", "api"}
    assert latest["eventId"]
    assert latest["status"] == "success"


def test_inbound_webhook_dispatches_workflow() -> None:
    headers = auth_headers()
    # Ensure an active workflow listens to webhook.inbound
    created = client.post(
        "/api/v1/workflows",
        headers=headers,
        json={
            "name": "Webhook Lot F",
            "status": "active",
            "definition": {
                "nodes": [
                    {
                        "id": "t1",
                        "type": "trigger",
                        "position": {"x": 0, "y": 0},
                        "data": {"label": "Webhook entrant", "kind": "trigger"},
                    },
                    {
                        "id": "a1",
                        "type": "action",
                        "position": {"x": 200, "y": 0},
                        "data": {"label": "Notifier Slack", "kind": "action"},
                    },
                ],
                "edges": [{"id": "e1", "source": "t1", "target": "a1"}],
            },
        },
    )
    assert created.status_code == 200

    endpoints = client.get("/api/v1/webhooks/endpoints", headers=headers).json()
    if not endpoints:
        created_ep = client.post(
            "/api/v1/webhooks/endpoints",
            headers=headers,
            json={"name": "Test WH", "description": "test", "eventTypes": []},
        )
        assert created_ep.status_code == 201
        endpoints = [created_ep.json()]

    token = endpoints[0]["token"]
    body = {"eventType": "webhook.inbound", "payload": {"hello": "world"}}
    raw = json.dumps(body).encode("utf-8")
    res = client.post(f"/api/v1/webhooks/inbound/{token}", content=raw, headers={"Content-Type": "application/json"})
    assert res.status_code == 200
    data = res.json()
    assert data["accepted"] is True
    assert data["eventId"]
    assert created.json()["id"] in data["triggeredWorkflowIds"]


def test_inbound_webhook_hmac_reject() -> None:
    headers = auth_headers()
    ep = client.post(
        "/api/v1/webhooks/endpoints",
        headers=headers,
        json={"name": "HMAC WH", "eventTypes": ["webhook.inbound"]},
    ).json()
    token = ep["token"]
    secret = ep["secret"]
    body = b'{"eventType":"webhook.inbound","payload":{}}'
    bad = client.post(
        f"/api/v1/webhooks/inbound/{token}",
        content=body,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": "sha256=deadbeef"},
    )
    assert bad.status_code == 401

    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    ok = client.post(
        f"/api/v1/webhooks/inbound/{token}",
        content=body,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": f"sha256={digest}"},
    )
    assert ok.status_code == 200


def test_tenant_isolation_events() -> None:
    ceo1 = auth_headers("ceo@demo.aibos.io")
    ceo2 = auth_headers("ceo@eu.aibos.io")
    client.post(
        "/api/v1/crm/leads",
        headers=ceo1,
        json={
            "title": "Org1 only",
            "company": "A",
            "contactName": "B",
            "value": 1,
            "expectedCloseDate": "2026-12-31T00:00:00Z",
        },
    )
    ev1 = client.get("/api/v1/events", headers=ceo1).json()
    ev2 = client.get("/api/v1/events", headers=ceo2).json()
    assert any(e["eventType"] == "crm.lead.created" for e in ev1)
    # org-2 should not see org-1 events
    assert all(e.get("payload", {}).get("title") != "Org1 only" for e in ev2)
