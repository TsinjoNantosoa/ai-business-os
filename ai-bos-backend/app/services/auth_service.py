from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services.session_store import InMemoryRefreshSessionStore, RefreshSession


@dataclass
class User:
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    permissions: list[str]
    org_id: str
    password_hash: str
    active: bool = True


class AuthService:
    def __init__(self, session_store: InMemoryRefreshSessionStore) -> None:
        self._sessions = session_store
        self._users_by_email: dict[str, User] = {}
        self._users_by_id: dict[str, User] = {}
        self._seed_demo_users()

    def _seed_demo_users(self) -> None:
        demo_users = [
            User(
                id="u-owner-1",
                email="ceo@demo.aibos.io",
                first_name="Aina",
                last_name="CEO",
                role="owner",
                permissions=[
                    "dashboard.read",
                    "ai.copilot.use",
                    "crm.contact.read",
                    "finance.invoice.read",
                    "settings.org",
                    "settings.team",
                    "admin.audit",
                ],
                org_id="org-demo-1",
                password_hash=hash_password("demo1234"),
            ),
            User(
                id="u-staff-1",
                email="staff@demo.aibos.io",
                first_name="Demo",
                last_name="Staff",
                role="staff",
                permissions=["dashboard.read"],
                org_id="org-demo-1",
                password_hash=hash_password("demo1234"),
            ),
        ]
        for user in demo_users:
            self._users_by_email[user.email.lower()] = user
            self._users_by_id[user.id] = user

    def _claims_for_user(self, user: User) -> dict[str, Any]:
        return {
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions,
            "org_id": user.org_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    def login(self, email: str, password: str) -> tuple[str, str]:
        user = self._users_by_email.get(email.lower().strip())
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
        if not user.active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

        if self._sessions.count_active_for_user(user.id) >= settings.max_refresh_sessions_per_user:
            self._sessions.revoke_all_for_user(user.id)

        session_id = secrets.token_hex(16)
        self._sessions.save(
            RefreshSession(
                session_id=session_id,
                user_id=user.id,
                created_at=datetime.now(tz=timezone.utc),
            )
        )

        access = create_access_token(user.id, self._claims_for_user(user))
        refresh = create_refresh_token(user.id, session_id)
        return access, refresh

    def refresh(self, refresh_token: str) -> tuple[str, str]:
        try:
            payload = decode_token(refresh_token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalide") from exc

        if payload.get("token_type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Type de token invalide")

        session_id = str(payload.get("sid", ""))
        user_id = str(payload.get("sub", ""))
        session = self._sessions.get(session_id)
        if not session or session.revoked or session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide")

        user = self._users_by_id.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

        # Rotate refresh token (single-use refresh)
        self._sessions.revoke(session_id)
        new_session_id = secrets.token_hex(16)
        self._sessions.save(
            RefreshSession(
                session_id=new_session_id,
                user_id=user.id,
                created_at=datetime.now(tz=timezone.utc),
            )
        )

        access = create_access_token(user.id, self._claims_for_user(user))
        refresh = create_refresh_token(user.id, new_session_id)
        return access, refresh

    def me_from_access_token(self, access_token: str) -> dict[str, Any]:
        try:
            payload = decode_token(access_token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token invalide") from exc

        user = self._users_by_id.get(str(payload.get("sub", "")))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

        return {
            "id": user.id,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "role": user.role,
            "permissions": user.permissions,
            "orgId": user.org_id,
        }

    def me_from_claims(self, claims: dict[str, Any]) -> dict[str, Any]:
        # Pour l'étape RBAC, on formate la "me" directement depuis les claims JWT.
        return {
            "id": str(claims.get("sub", "")),
            "email": claims.get("email"),
            "firstName": claims.get("first_name"),
            "lastName": claims.get("last_name"),
            "role": claims.get("role"),
            "permissions": claims.get("permissions") or [],
            "orgId": claims.get("org_id"),
        }

    def list_users_for_rbac(self) -> list[dict[str, Any]]:
        users = sorted(self._users_by_id.values(), key=lambda u: u.id)
        return [
            {
                "id": u.id,
                "email": u.email,
                "role": u.role,
                "orgId": u.org_id,
                "active": u.active,
            }
            for u in users
        ]

    def roles_and_permissions_for_rbac(self) -> tuple[list[dict[str, Any]], list[str]]:
        role_to_perms: dict[str, set[str]] = {}
        for u in self._users_by_id.values():
            perms = role_to_perms.setdefault(u.role, set())
            perms.update(u.permissions)

        roles = []
        permissions_set: set[str] = set()
        for role, perms in sorted(role_to_perms.items(), key=lambda x: x[0]):
            permissions_list = sorted(perms)
            roles.append({"name": role, "permissions": permissions_list})
            permissions_set.update(perms)

        return roles, sorted(permissions_set)
