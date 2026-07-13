from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.services.bootstrap import bootstrap_demo_data

client = TestClient(app)


def test_bootstrap_creates_demo_org_and_users() -> None:
    with SessionLocal() as session:
        orgs = OrganizationRepository(session).list_all()
        users = UserRepository(session).list_all()

    assert len(orgs) >= 1
    assert any(org.id == "org-1" for org in orgs)
    assert len(users) >= 2
    assert any(user.email == "ceo@demo.aibos.io" for user in users)


def test_users_are_scoped_to_organization() -> None:
    with SessionLocal() as session:
        users = UserRepository(session).list_all()
        org_ids = {user.org_id for user in users}

    assert "org-1" in org_ids
    for user in users:
        assert user.org_id


def test_bootstrap_is_idempotent() -> None:
    with SessionLocal() as session:
        before = OrganizationRepository(session).count()
        bootstrap_demo_data(session)
        after = OrganizationRepository(session).count()
    assert before == after


def test_login_uses_database_user() -> None:
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@demo.aibos.io", "password": "demo1234"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["user"]["orgId"] == "org-1"


def test_platform_organizations_from_database() -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "ceo@demo.aibos.io", "password": "demo1234"},
    )
    token = login.json()["token"]
    res = client.get(
        "/api/v1/platform/organizations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    orgs = res.json()
    assert orgs[0]["id"] == "org-1"
    assert orgs[0]["name"] == "Acme Corp"
    assert len(orgs) == 1  # tenant isolation: only caller's org
