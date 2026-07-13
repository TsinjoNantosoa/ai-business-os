from __future__ import annotations

import json

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


def test_billing_requires_permission() -> None:
    token = login("staff@demo.aibos.io")
    res = client.get("/api/v1/billing/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_billing_overview_owner() -> None:
    token = login()
    res = client.get("/api/v1/billing/overview", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body["subscription"]["plan"]["code"] in {"enterprise", "pro", "starter"}
    assert body["subscription"]["usage"]["seats"]["used"] >= 1
    assert len(body["invoices"]) >= 4


def test_billing_plans_and_checkout() -> None:
    token = login()
    headers = {"Authorization": f"Bearer {token}"}
    plans = client.get("/api/v1/billing/plans", headers=headers)
    assert plans.status_code == 200
    assert len(plans.json()) == 3

    checkout = client.post(
        "/api/v1/billing/checkout",
        headers=headers,
        json={"planCode": "pro"},
    )
    assert checkout.status_code == 200
    body = checkout.json()
    assert body["checkoutUrl"]
    assert body["sessionId"]


def test_stripe_webhook_checkout_completed() -> None:
    payload = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"org_id": "org-1", "plan_code": "pro"},
                "customer": "cus_test_1",
                "subscription": "sub_test_1",
            }
        },
    }
    res = client.post(
        "/api/v1/billing/webhooks/stripe",
        content=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 200

    token = login()
    overview = client.get(
        "/api/v1/billing/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert overview.json()["subscription"]["plan"]["code"] == "pro"
