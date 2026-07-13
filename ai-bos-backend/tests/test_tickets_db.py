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


def test_tickets_list_from_db() -> None:
    res = client.get("/api/v1/support/tickets", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 10
    assert body[0]["ticketNumber"].startswith("TKT-")
    assert body[0]["messages"]


def test_ticket_reply_message() -> None:
    headers = auth_headers()
    tickets = client.get("/api/v1/support/tickets", headers=headers).json()
    ticket_id = tickets[0]["id"]
    before = len(tickets[0]["messages"])

    res = client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        headers=headers,
        json={"content": "Nous avons corrigé le problème. Merci de votre patience."},
    )
    assert res.status_code == 201
    body = res.json()
    assert len(body["messages"]) == before + 1
    assert body["messages"][-1]["content"].startswith("Nous avons corrigé")


def test_ticket_status_update() -> None:
    headers = auth_headers()
    tickets = client.get("/api/v1/support/tickets", headers=headers).json()
    ticket_id = tickets[1]["id"]
    res = client.patch(
        f"/api/v1/support/tickets/{ticket_id}/status",
        headers=headers,
        json={"status": "resolved"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "resolved"
