from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str) -> str:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "demo1234"},
    )
    assert res.status_code == 200
    return res.json()["token"]


def test_crm_contacts_requires_auth() -> None:
    res = client.get("/api/v1/crm/contacts")
    assert res.status_code == 401


def test_crm_contacts_owner_ok() -> None:
    token = login("ceo@demo.aibos.io")
    res = client.get("/api/v1/crm/contacts", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)
    assert body[0]["id"]
    assert body[0]["company"]


def test_finance_invoices_staff_ok() -> None:
    token = login("staff@demo.aibos.io")
    res = client.get("/api/v1/finance/invoices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body and body[0]["invoiceNumber"]


def test_finance_transactions_owner_ok() -> None:
    token = login("ceo@demo.aibos.io")
    res = client.get("/api/v1/finance/transactions", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body and body[0]["type"]


def test_sales_and_marketing_ok() -> None:
    token = login("ceo@demo.aibos.io")
    sales = client.get("/api/v1/sales/orders", headers={"Authorization": f"Bearer {token}"})
    marketing = client.get("/api/v1/marketing/campaigns", headers={"Authorization": f"Bearer {token}"})
    assert sales.status_code == 200
    assert marketing.status_code == 200


def test_bi_reports_ok() -> None:
    token = login("ceo@demo.aibos.io")
    res = client.get("/api/v1/bi/reports", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    body = res.json()
    assert body and body[0]["chartType"]

