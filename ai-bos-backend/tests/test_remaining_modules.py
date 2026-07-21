from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ALL_PROTECTED_PATHS = [
    "/api/v1/platform/organizations",
    "/api/v1/platform/notifications",
    "/api/v1/platform/audit-logs",
    "/api/v1/finance/overview",
    "/api/v1/crm/leads",
    "/api/v1/crm/activities",
    "/api/v1/crm/contacts",
    "/api/v1/support/tickets",
    "/api/v1/hr/employees",
    "/api/v1/hr/jobs",
    "/api/v1/hr/candidates",
    "/api/v1/sales/orders",
    "/api/v1/marketing/campaigns",
    "/api/v1/finance/invoices",
    "/api/v1/finance/transactions",
    "/api/v1/bi/reports",
    "/api/v1/tasks",
    "/api/v1/projects",
    "/api/v1/calendar/events",
    "/api/v1/meetings",
    "/api/v1/contracts",
    "/api/v1/knowledge/articles",
    "/api/v1/workflows",
    "/api/v1/ai/agents",
    "/api/v1/inventory/items",
    "/api/v1/documents",
    "/api/v1/analytics/kpis",
    "/api/v1/procurement/suppliers",
    "/api/v1/procurement/purchase-orders",
]


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "demo1234"},
    )
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token or login()}"}


def test_all_frontend_paths_require_auth() -> None:
    for path in ALL_PROTECTED_PATHS:
        res = client.get(path)
        assert res.status_code == 401, f"{path} should require auth"


def test_all_frontend_paths_ok_for_owner() -> None:
    headers = auth_headers()
    for path in ALL_PROTECTED_PATHS:
        res = client.get(path, headers=headers)
        assert res.status_code == 200, f"{path} => {res.status_code} {res.text}"


def test_platform_notifications_shape() -> None:
    res = client.get("/api/v1/platform/notifications", headers=auth_headers())
    body = res.json()
    assert len(body) >= 3
    assert body[0]["type"] in {"info", "warning", "success", "error"}
    assert "title" in body[0]


def test_platform_audit_logs_shape() -> None:
    res = client.get("/api/v1/platform/audit-logs", headers=auth_headers())
    body = res.json()
    assert len(body) >= 30
    assert "action" in body[0]


def test_hr_recruitment_shape() -> None:
    headers = auth_headers()
    jobs = client.get("/api/v1/hr/jobs", headers=headers).json()
    candidates = client.get("/api/v1/hr/candidates", headers=headers).json()
    assert len(jobs) >= 10
    assert jobs[0]["title"]
    assert len(candidates) >= 20
    assert candidates[0]["stage"]


def test_operations_modules_shape() -> None:
    headers = auth_headers()
    contracts = client.get("/api/v1/contracts", headers=headers).json()
    articles = client.get("/api/v1/knowledge/articles", headers=headers).json()
    workflows = client.get("/api/v1/workflows", headers=headers).json()
    agents = client.get("/api/v1/ai/agents", headers=headers).json()
    inventory = client.get("/api/v1/inventory/items", headers=headers).json()
    documents = client.get("/api/v1/documents", headers=headers).json()

    assert len(contracts) >= 12
    assert len(articles) >= 12
    assert len(workflows) >= 5
    assert len(agents) >= 5
    assert len(inventory) >= 10
    assert documents[0]["type"] == "folder"


def test_analytics_and_forecast() -> None:
    headers = auth_headers()
    analytics = client.get("/api/v1/analytics/kpis", headers=headers).json()
    assert len(analytics["kpis"]) == 6
    assert "revenue" in analytics

    for horizon, expected_len in [("7d", 7), ("30d", 30), ("90d", 90)]:
        res = client.get(f"/api/v1/ml/forecast?horizon={horizon}", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["horizon"] == horizon
        assert len(body["data"]) == expected_len


def test_forecast_invalid_horizon() -> None:
    res = client.get("/api/v1/ml/forecast?horizon=1y", headers=auth_headers())
    assert res.status_code == 422


def test_procurement_shape() -> None:
    headers = auth_headers()
    suppliers = client.get("/api/v1/procurement/suppliers", headers=headers).json()
    orders = client.get("/api/v1/procurement/purchase-orders", headers=headers).json()
    assert len(suppliers) == 14
    assert len(orders) == 22
    assert orders[0]["poNumber"].startswith("PO-")
