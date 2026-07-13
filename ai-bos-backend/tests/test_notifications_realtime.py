from __future__ import annotations

import json
import threading
import time

from fastapi.testclient import TestClient

from app.main import app
from app.services.notification_hub import notification_hub
from app.services.notification_service import create_and_publish_notification
from app.core.database import SessionLocal

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_list_notifications_from_db() -> None:
    res = client.get("/api/v1/platform/notifications", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 5
    assert body[0]["title"]
    assert "read" in body[0]


def test_mark_one_and_all_read() -> None:
    headers = auth_headers()
    items = client.get("/api/v1/platform/notifications", headers=headers).json()
    unread = next((n for n in items if not n["read"]), None)
    assert unread is not None

    marked = client.post(f"/api/v1/platform/notifications/{unread['id']}/read", headers=headers)
    assert marked.status_code == 200
    assert marked.json()["read"] is True

    result = client.post("/api/v1/platform/notifications/read-all", headers=headers)
    assert result.status_code == 200
    assert result.json()["updated"] >= 0

    after = client.get("/api/v1/platform/notifications", headers=headers).json()
    assert all(n["read"] for n in after)


def test_create_contact_publishes_notification() -> None:
    headers = auth_headers()
    before = len(client.get("/api/v1/platform/notifications", headers=headers).json())
    create = client.post(
        "/api/v1/crm/contacts",
        headers=headers,
        json={
            "firstName": "Notif",
            "lastName": "User",
            "email": f"notif.user.{int(time.time()*1000)}@example.com",
            "company": "NotifCo",
        },
    )
    assert create.status_code == 201
    after = client.get("/api/v1/platform/notifications", headers=headers).json()
    assert len(after) == before + 1
    assert after[0]["title"] == "Nouveau contact"


def test_sse_stream_receives_notification() -> None:
    token = login()

    def publisher() -> None:
        time.sleep(0.3)
        with SessionLocal() as session:
            create_and_publish_notification(
                session,
                org_id="org-1",
                type="success",
                title="SSE Test",
                message="Hello realtime",
                link="/app/inbox",
            )

    thread = threading.Thread(target=publisher, daemon=True)
    thread.start()

    with client.stream(
        "GET",
        "/api/v1/platform/notifications/stream",
        params={"access_token": token, "max_events": 2},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
        text = "".join(response.iter_text())

    thread.join(timeout=2)
    assert '"type": "connected"' in text or '"type":"connected"' in text
    assert "SSE Test" in text
    assert '"type": "notification"' in text or '"type":"notification"' in text


def test_hub_unsubscribe_cleanup() -> None:
    q = notification_hub.subscribe("org-test-cleanup")
    notification_hub.publish("org-test-cleanup", {"type": "ping"})
    assert q.get_nowait()["type"] == "ping"
    notification_hub.unsubscribe("org-test-cleanup", q)
