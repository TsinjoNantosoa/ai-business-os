from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def login(email: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "demo1234"})
    assert res.status_code == 200
    return res.json()["token"]


def headers(email: str, *, tenant: str | None = None) -> dict[str, str]:
    h = {"Authorization": f"Bearer {login(email)}"}
    if tenant is not None:
        h["X-Tenant-Id"] = tenant
    return h


def test_tenant_header_mismatch_forbidden() -> None:
    res = client.get(
        "/api/v1/crm/contacts",
        headers=headers("ceo@demo.aibos.io", tenant="org-2"),
    )
    assert res.status_code == 403


def test_tenant_header_match_ok() -> None:
    res = client.get(
        "/api/v1/crm/contacts",
        headers=headers("ceo@demo.aibos.io", tenant="org-1"),
    )
    assert res.status_code == 200


def test_org1_cannot_see_org2_contact() -> None:
    org1 = client.get("/api/v1/crm/contacts", headers=headers("ceo@demo.aibos.io")).json()
    org2 = client.get("/api/v1/crm/contacts", headers=headers("ceo@eu.aibos.io")).json()

    org1_ids = {c["id"] for c in org1}
    org2_ids = {c["id"] for c in org2}
    assert "contact-org2-1" in org2_ids
    assert "contact-org2-1" not in org1_ids
    assert org1_ids.isdisjoint(org2_ids)


def test_org1_cannot_fetch_org2_contact_by_id() -> None:
    res = client.get(
        "/api/v1/crm/contacts/contact-org2-1",
        headers=headers("ceo@demo.aibos.io"),
    )
    # list endpoint may not have get by id — try patch which uses get_by_id
    res = client.patch(
        "/api/v1/crm/contacts/contact-org2-1",
        headers=headers("ceo@demo.aibos.io"),
        json={"firstName": "Hacked"},
    )
    assert res.status_code == 404


def test_organizations_only_own_tenant() -> None:
    res = client.get("/api/v1/platform/organizations", headers=headers("ceo@demo.aibos.io"))
    assert res.status_code == 200
    assert [o["id"] for o in res.json()] == ["org-1"]

    res2 = client.get("/api/v1/platform/organizations", headers=headers("ceo@eu.aibos.io"))
    assert res2.status_code == 200
    assert [o["id"] for o in res2.json()] == ["org-2"]


def test_rbac_users_scoped_to_tenant() -> None:
    res = client.get("/api/v1/rbac/users", headers=headers("ceo@demo.aibos.io"))
    assert res.status_code == 200
    emails = {u["email"] for u in res.json()["items"]}
    assert "ceo@demo.aibos.io" in emails
    assert "ceo@eu.aibos.io" not in emails


def test_cannot_assign_task_to_other_tenant_user() -> None:
    tasks = client.get("/api/v1/tasks", headers=headers("ceo@demo.aibos.io")).json()
    assert tasks
    task_id = tasks[0]["id"]
    res = client.patch(
        f"/api/v1/tasks/{task_id}/assign",
        headers=headers("ceo@demo.aibos.io"),
        json={"assigneeId": "u-owner-2", "assigneeName": "Anna Schmidt"},
    )
    assert res.status_code == 404
