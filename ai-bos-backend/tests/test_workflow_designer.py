"""Lot E / S32 — workflow designer CRUD + definition graph."""

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


def _sample_definition() -> dict:
    return {
        "nodes": [
            {
                "id": "trigger-1",
                "type": "trigger",
                "position": {"x": 40, "y": 80},
                "data": {"label": "Lead créé", "kind": "trigger"},
            },
            {
                "id": "action-1",
                "type": "action",
                "position": {"x": 260, "y": 80},
                "data": {"label": "Envoyer email", "kind": "action"},
            },
            {
                "id": "action-2",
                "type": "action",
                "position": {"x": 480, "y": 80},
                "data": {"label": "Créer tâche", "kind": "action"},
            },
        ],
        "edges": [
            {"id": "e1", "source": "trigger-1", "target": "action-1"},
            {"id": "e2", "source": "action-1", "target": "action-2"},
        ],
    }


def test_create_workflow_with_definition() -> None:
    res = client.post(
        "/api/v1/workflows",
        headers=auth_headers(),
        json={
            "name": "Designer Lot E",
            "description": "Créé via canvas",
            "status": "draft",
            "definition": _sample_definition(),
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Designer Lot E"
    assert body["trigger"] == "Lead créé"
    assert body["actions"] == ["Envoyer email", "Créer tâche"]
    assert len(body["definition"]["nodes"]) == 3
    assert len(body["definition"]["edges"]) == 2


def test_patch_and_get_workflow() -> None:
    created = client.post(
        "/api/v1/workflows",
        headers=auth_headers(),
        json={"name": "À éditer", "status": "draft", "definition": _sample_definition()},
    ).json()
    wf_id = created["id"]

    patched = client.patch(
        f"/api/v1/workflows/{wf_id}",
        headers=auth_headers(),
        json={
            "name": "Édité",
            "status": "active",
            "definition": {
                "nodes": [
                    {
                        "id": "trigger-1",
                        "type": "trigger",
                        "position": {"x": 0, "y": 0},
                        "data": {"label": "Manuel", "kind": "trigger"},
                    },
                    {
                        "id": "action-1",
                        "type": "action",
                        "position": {"x": 200, "y": 0},
                        "data": {"label": "Notifier Slack", "kind": "action"},
                    },
                ],
                "edges": [{"id": "e1", "source": "trigger-1", "target": "action-1"}],
            },
        },
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["name"] == "Édité"
    assert body["status"] == "active"
    assert body["trigger"] == "Manuel"
    assert body["actions"] == ["Notifier Slack"]

    fetched = client.get(f"/api/v1/workflows/{wf_id}", headers=auth_headers())
    assert fetched.status_code == 200
    assert fetched.json()["id"] == wf_id


def test_list_includes_definition_for_seeded() -> None:
    res = client.get("/api/v1/workflows", headers=auth_headers())
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1
    assert "definition" in items[0]
    assert "nodes" in items[0]["definition"]


def test_run_after_activate() -> None:
    created = client.post(
        "/api/v1/workflows",
        headers=auth_headers(),
        json={"name": "Runnable", "status": "active", "definition": _sample_definition()},
    ).json()
    run = client.post(f"/api/v1/workflows/{created['id']}/run", headers=auth_headers())
    assert run.status_code == 200
    assert run.json()["execution"]["status"] == "success"
