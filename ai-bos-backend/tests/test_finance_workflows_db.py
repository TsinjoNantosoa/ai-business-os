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


def test_finance_invoices_list_from_db() -> None:
    res = client.get("/api/v1/finance/invoices", headers=auth_headers())
    assert res.status_code == 200
    body = res.json()
    assert len(body) >= 15
    assert body[0]["invoiceNumber"].startswith("INV-")
    assert body[0]["lineItems"]


def test_finance_invoice_create_and_send() -> None:
    headers = auth_headers()
    create = client.post(
        "/api/v1/finance/invoices",
        headers=headers,
        json={
            "clientId": "contact-1",
            "clientName": "Acme Test",
            "lineItems": [
                {"description": "Consulting", "quantity": 2, "unitPrice": 500, "taxRate": 20},
            ],
        },
    )
    assert create.status_code == 201
    invoice = create.json()
    assert invoice["status"] == "draft"
    assert invoice["totalAmount"] == 1200

    send = client.post(f"/api/v1/finance/invoices/{invoice['id']}/send", headers=headers)
    assert send.status_code == 200
    assert send.json()["status"] == "sent"


def test_workflows_list_and_run() -> None:
    headers = auth_headers()
    list_res = client.get("/api/v1/workflows", headers=headers)
    assert list_res.status_code == 200
    workflows = list_res.json()
    assert len(workflows) >= 5

    active = next(wf for wf in workflows if wf["status"] == "active")
    run_res = client.post(f"/api/v1/workflows/{active['id']}/run", headers=headers)
    assert run_res.status_code == 200
    body = run_res.json()
    assert body["execution"]["status"] == "success"
    assert body["workflow"]["runCount"] == active["runCount"] + 1

    exec_res = client.get("/api/v1/workflows/executions", headers=headers)
    assert exec_res.status_code == 200
    executions = exec_res.json()
    assert len(executions) >= 1
    assert executions[0]["workflowName"]
