"""Catalog CRUD mutations — HR, inventory, procurement, accounting."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def login(email: str = "ceo@demo.aibos.io") -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def auth_headers(email: str = "ceo@demo.aibos.io") -> dict[str, str]:
    return {"Authorization": f"Bearer {login(email)}"}


def test_create_and_patch_employee() -> None:
    headers = auth_headers()
    created = client.post(
        "/api/v1/hr/employees",
        headers=headers,
        json={
            "firstName": "Alice",
            "lastName": "Martin",
            "email": "alice.martin.catalog@example.com",
            "position": "Analyste",
            "department": "Finance",
            "salary": 42000,
            "location": "Paris",
        },
    )
    assert created.status_code == 201, created.text
    emp = created.json()
    assert emp["firstName"] == "Alice"
    assert emp["salary"] == 42000

    patched = client.patch(
        f"/api/v1/hr/employees/{emp['id']}",
        headers=headers,
        json={"status": "on_leave", "salary": 43000},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "on_leave"
    assert patched.json()["salary"] == 43000


def test_create_job_and_candidate() -> None:
    headers = auth_headers()
    job = client.post(
        "/api/v1/hr/jobs",
        headers=headers,
        json={
            "title": "Dev Fullstack",
            "department": "Engineering",
            "location": "Remote",
            "type": "full_time",
        },
    )
    assert job.status_code == 201, job.text
    job_id = job.json()["id"]

    cand = client.post(
        "/api/v1/hr/candidates",
        headers=headers,
        json={
            "name": "Bob Dupont",
            "email": "bob.dupont.catalog@example.com",
            "jobId": job_id,
            "jobTitle": "Dev Fullstack",
            "stage": "screening",
            "score": 80,
        },
    )
    assert cand.status_code == 201, cand.text
    patched = client.patch(
        f"/api/v1/hr/candidates/{cand.json()['id']}",
        headers=headers,
        json={"stage": "interview"},
    )
    assert patched.status_code == 200
    assert patched.json()["stage"] == "interview"


def test_create_inventory_item() -> None:
    headers = auth_headers()
    res = client.post(
        "/api/v1/inventory/items",
        headers=headers,
        json={
            "sku": "SKU-CAT-1",
            "name": "Clavier méca",
            "category": "IT",
            "quantity": 5,
            "reorderLevel": 10,
            "warehouse": "Paris",
            "unitPrice": 89.9,
        },
    )
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["sku"] == "SKU-CAT-1"
    assert body["status"] == "low_stock"


def test_create_supplier_and_purchase_order() -> None:
    headers = auth_headers()
    supplier = client.post(
        "/api/v1/procurement/suppliers",
        headers=headers,
        json={
            "name": "Acme Supplies",
            "email": "orders@acme-supplies.test",
            "country": "FR",
            "rating": 4.5,
        },
    )
    assert supplier.status_code == 201, supplier.text
    sid = supplier.json()["id"]

    po = client.post(
        "/api/v1/procurement/purchase-orders",
        headers=headers,
        json={
            "supplierId": sid,
            "supplierName": "Acme Supplies",
            "totalAmount": 1500,
            "itemCount": 3,
            "status": "draft",
        },
    )
    assert po.status_code == 201, po.text
    assert po.json()["poNumber"].startswith("PO-")
    assert po.json()["supplierName"] == "Acme Supplies"


def test_create_and_patch_transaction() -> None:
    headers = auth_headers()
    created = client.post(
        "/api/v1/finance/transactions",
        headers=headers,
        json={
            "description": "Achat licences",
            "amount": 299.5,
            "type": "expense",
            "category": "Software",
            "account": "Banque",
        },
    )
    assert created.status_code == 201, created.text
    tx = created.json()
    patched = client.patch(
        f"/api/v1/finance/transactions/{tx['id']}",
        headers=headers,
        json={"amount": 320},
    )
    assert patched.status_code == 200
    assert patched.json()["amount"] == 320


def test_employee_write_forbidden_for_staff_without_perm() -> None:
    headers = auth_headers("staff@demo.aibos.io")
    res = client.post(
        "/api/v1/hr/employees",
        headers=headers,
        json={
            "firstName": "X",
            "lastName": "Y",
            "email": "xy@example.com",
            "position": "Intern",
            "department": "HR",
        },
    )
    assert res.status_code in {403, 401}
