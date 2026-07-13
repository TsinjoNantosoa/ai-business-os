from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User as UserModel
from app.repositories.user_repository import UserRepository
from app.services.session_store import InMemoryRefreshSessionStore, RefreshSession


class AuthService:
    def __init__(self, session_store: InMemoryRefreshSessionStore) -> None:
        self._sessions = session_store

    def _claims_for_user(self, user: UserModel) -> dict[str, Any]:
        return {
            "email": user.email,
            "role": user.role,
            "permissions": user.permissions or [],
            "org_id": user.org_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }

    def _get_user_by_email(self, email: str) -> UserModel | None:
        with SessionLocal() as session:
            return UserRepository(session).get_by_email(email)

    def _get_user_by_id(self, user_id: str) -> UserModel | None:
        with SessionLocal() as session:
            return UserRepository(session).get_by_id(user_id)

    def login(self, email: str, password: str) -> tuple[str, str]:
        user = self._get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
        if not user.active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")
        return self._issue_tokens(user)

    def login_oauth_profile(
        self,
        *,
        provider: str,
        subject: str,
        email: str,
        first_name: str,
        last_name: str,
    ) -> tuple[str, str]:
        from app.core.security import hash_password
        from app.repositories.oauth_identity_repository import OAuthIdentityRepository
        from app.services.role_permissions import permissions_for_role

        email = email.lower().strip()
        if not email or not subject:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profil OAuth incomplet")

        with SessionLocal() as session:
            oauth_repo = OAuthIdentityRepository(session)
            user_repo = UserRepository(session)
            identity = oauth_repo.get_by_provider_subject(provider, subject)
            user: UserModel | None = None
            if identity:
                user = user_repo.get_by_id(identity.user_id)
            if not user:
                user = user_repo.get_by_email(email)
            if not user:
                # New OAuth users join demo org-1 as staff (invitation flow preferred in prod).
                user = user_repo.create(
                    org_id="org-1",
                    email=email,
                    first_name=first_name or "OAuth",
                    last_name=last_name or provider.title(),
                    role="staff",
                    permissions=permissions_for_role("staff"),
                    password_hash=hash_password(secrets.token_urlsafe(24)),
                )
            if not user.active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

            oauth_repo.upsert(
                user_id=user.id,
                org_id=user.org_id,
                provider=provider,
                provider_subject=subject,
                email=email,
            )
            user_id = user.id

        user = self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")
        return self._issue_tokens(user)

    def _issue_tokens(self, user: UserModel) -> tuple[str, str]:
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

        user = self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

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

        user = self._get_user_by_id(str(payload.get("sub", "")))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

        return self._user_to_me(user)

    def me_from_claims(self, claims: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(claims.get("sub", "")),
            "email": claims.get("email"),
            "firstName": claims.get("first_name"),
            "lastName": claims.get("last_name"),
            "role": claims.get("role"),
            "permissions": claims.get("permissions") or [],
            "orgId": claims.get("org_id"),
        }

    def list_users_for_rbac(self, org_id: str | None = None) -> list[dict[str, Any]]:
        with SessionLocal() as session:
            if org_id:
                users = UserRepository(session).list_by_org(org_id)
            else:
                users = UserRepository(session).list_all()
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

    def roles_and_permissions_for_rbac(self, org_id: str | None = None) -> tuple[list[dict[str, Any]], list[str]]:
        with SessionLocal() as session:
            if org_id:
                users = UserRepository(session).list_by_org(org_id)
            else:
                users = UserRepository(session).list_all()

        role_to_perms: dict[str, set[str]] = {}
        for user in users:
            perms = role_to_perms.setdefault(user.role, set())
            perms.update(user.permissions or [])

        roles = []
        permissions_set: set[str] = set()
        for role, perms in sorted(role_to_perms.items(), key=lambda x: x[0]):
            permissions_list = sorted(perms)
            roles.append({"name": role, "permissions": permissions_list})
            permissions_set.update(perms)

        return roles, sorted(permissions_set)

    @staticmethod
    def _user_to_me(user: UserModel) -> dict[str, Any]:
        return {
            "id": user.id,
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "role": user.role,
            "permissions": user.permissions or [],
            "orgId": user.org_id,
        }
