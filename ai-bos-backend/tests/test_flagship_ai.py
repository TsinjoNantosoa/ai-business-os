from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_executive_daily_brief_is_grounded() -> None:
    response = client.get("/api/v1/ai/insights/executive-brief", headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"topPriorities", "risks", "opportunities", "recommendedActions", "method"}
    for section in ("topPriorities", "risks", "opportunities"):
        assert all(item.get("source") for item in body[section])


def test_cashflow_intelligence_explains_drivers() -> None:
    response = client.get("/api/v1/ai/insights/cashflow", headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert body["risk"]["level"] in {"low", "medium", "high"}
    assert body["risk"]["why"]
    assert all(driver["source"] for driver in body["drivers"])
    assert len(body["recommendations"]) >= 3


def test_sales_risk_is_heuristic_and_explainable() -> None:
    response = client.get("/api/v1/ai/insights/sales-risk", headers=_headers())
    assert response.status_code == 200
    body = response.json()
    assert "heuristique" in body["method"].lower()
    for deal in body["deals"]:
        assert 0 <= deal["riskScore"] <= 100
        assert deal["reasons"]
        assert deal["source"] == "crm.leads"

