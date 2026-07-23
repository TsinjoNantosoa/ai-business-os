"""S35 — plan RPM + monthly token hard quotas."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.repositories.billing_repository import BillingRepository
from app.services.quota_service import reset_plan_rpm_limiter

client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_limiter_and_mock_llm(monkeypatch):
    reset_plan_rpm_limiter()
    monkeypatch.setattr(settings, "openai_api_key", None)
    yield
    reset_plan_rpm_limiter()


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    headers = {"Authorization": f"Bearer {login(email)}"}
    if settings.chatbot_api_token:
        headers["X-Chatbot-Token"] = settings.chatbot_api_token
    return headers


def test_billing_quotas_endpoint() -> None:
    res = client.get("/api/v1/billing/quotas", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["planCode"] in {"starter", "pro", "enterprise"}
    assert body["aiRpm"] >= 10
    assert "aiTokens" in body["usage"]
    assert "tokensRemaining" in body


def test_overview_includes_quotas_and_live_tokens() -> None:
    res = client.get("/api/v1/billing/overview", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert body["quotas"] is not None
    assert body["subscription"]["plan"]["aiRpm"] >= 10
    assert "aiTokens" in body["subscription"]["usage"]


def test_rpm_hard_limit_returns_429() -> None:
    headers = auth_headers()
    # Force tiny RPM on current plan
    with SessionLocal() as db:
        sub = BillingRepository(db).get_subscription_for_org("org-1")
        assert sub and sub.plan
        sub.plan.ai_rpm = 2
        db.commit()

    reset_plan_rpm_limiter()
    ok1 = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "ping 1"},
    )
    ok2 = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "ping 2"},
    )
    # Streaming endpoints may return 200 immediately; drain or use status
    assert ok1.status_code in {200, 429}
    assert ok2.status_code in {200, 429}

    blocked = client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json={"message": "ping 3"},
    )
    assert blocked.status_code == 429
    assert "Limite plan" in blocked.json()["detail"] or "requêtes IA" in blocked.json()["detail"]

    # restore
    with SessionLocal() as db:
        sub = BillingRepository(db).get_subscription_for_org("org-1")
        if sub and sub.plan:
            sub.plan.ai_rpm = 60
            db.commit()


def test_token_quota_exhausted_returns_429() -> None:
    headers = auth_headers()
    with SessionLocal() as db:
        sub = BillingRepository(db).get_subscription_for_org("org-1")
        assert sub and sub.plan
        sub.plan.ai_tokens_limit = 1
        # Ensure period includes now; leave traces possibly > 1 after previous chats
        db.commit()

    # Create at least one chat so usage >= 1
    client.post("/api/v1/ai/chat", headers=headers, json={"message": "consume tokens"})
    blocked = client.post("/api/v1/ai/chat", headers=headers, json={"message": "should block"})
    assert blocked.status_code == 429
    detail = blocked.json()["detail"]
    assert "Quota tokens" in detail or "tokens IA" in detail

    with SessionLocal() as db:
        sub = BillingRepository(db).get_subscription_for_org("org-1")
        if sub and sub.plan:
            sub.plan.ai_tokens_limit = 1_000_000
            db.commit()
