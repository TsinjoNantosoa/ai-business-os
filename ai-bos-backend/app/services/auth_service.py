from __future__ import annotations

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User as UserModel
from app.repositories.password_reset_repository import PasswordResetRepository, hash_reset_token
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app.services.session_store import (
    DatabaseRefreshSessionStore,
    RefreshSession,
    hash_refresh_token,
)


logger = logging.getLogger("aibos.auth")


class AuthService:
    def __init__(
        self,
        session_store: DatabaseRefreshSessionStore,
        email_service: EmailService,
    ) -> None:
        self._sessions = session_store
        self.email_service = email_service

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
            self._set_auth_lookup(session, "app.auth_email", email.lower().strip())
            return UserRepository(session).get_by_email(email)

    def _get_user_by_id(self, user_id: str) -> UserModel | None:
        with SessionLocal() as session:
            self._set_auth_lookup(session, "app.auth_user_id", user_id)
            return UserRepository(session).get_by_id(user_id)

    @staticmethod
    def _set_auth_lookup(session, name: str, value: str) -> None:
        if not settings.is_sqlite:
            from sqlalchemy import text

            session.execute(text("SELECT set_config(:name, :value, true)"), {"name": name, "value": value})

    def login(self, email: str, password: str) -> tuple[str, str]:
        user = self._get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
        if not user.active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")
        return self._issue_tokens(user)

    def register(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        organization_name: str,
    ) -> tuple[str, str]:
        """Create a new organization + owner account, then issue tokens."""
        from datetime import timedelta

        from app.models.user import User as UserOrm
        from app.repositories.billing_repository import BillingRepository
        from app.repositories.organization_repository import OrganizationRepository
        from app.services.role_permissions import OWNER_PERMISSIONS

        email_norm = email.lower().strip()
        org_name = organization_name.strip()
        first = first_name.strip()
        last = last_name.strip()
        if not org_name or not first or not last:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Champs obligatoires manquants")
        if len(password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le mot de passe doit contenir au moins 6 caractères",
            )

        with SessionLocal() as session:
            self._set_auth_lookup(session, "app.auth_email", email_norm)
            if UserRepository(session).get_by_email(email_norm):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Un compte avec cet email existe déjà",
                )

            org_id = f"org-{secrets.token_hex(8)}"
            user_id = f"u-{secrets.token_hex(8)}"
            OrganizationRepository(session).create(org_id=org_id, name=org_name)
            self._set_auth_lookup(session, "app.current_org_id", org_id)

            user = UserOrm(
                id=user_id,
                org_id=org_id,
                email=email_norm,
                first_name=first,
                last_name=last,
                role="owner",
                permissions=list(OWNER_PERMISSIONS),
                password_hash=hash_password(password),
                active=True,
            )
            session.add(user)

            billing = BillingRepository(session)
            plan = billing.get_plan_by_code("starter") or billing.get_plan_by_id("plan-starter")
            if plan is None and billing.plans_count() == 0:
                from app.models.billing import BillingPlan

                plan = BillingPlan(
                    id="plan-starter",
                    code="starter",
                    name="Starter",
                    price_monthly=0,
                    currency="EUR",
                    seats_limit=5,
                    ai_tokens_limit=100_000,
                    ai_rpm=20,
                    storage_gb_limit=10,
                    stripe_price_id=None,
                )
                session.add(plan)
                session.flush()
            if plan is not None:
                now = datetime.now(timezone.utc)
                billing.create_subscription(
                    subscription_id=f"sub-{secrets.token_hex(8)}",
                    org_id=org_id,
                    plan_id=plan.id,
                    status="active",
                    period_start=now,
                    period_end=now + timedelta(days=30),
                    seats_used=1,
                    ai_tokens_used=0,
                    storage_gb_used=0,
                )

            from app.services.org_demo_data import ensure_org_demo_agents, ensure_org_demo_datasets

            ensure_org_demo_datasets(session, org_id)
            ensure_org_demo_agents(session, org_id)

            session.commit()
            session.refresh(user)
            user_snapshot = user

        return self._issue_tokens(user_snapshot)

    def request_password_reset(self, email: str) -> None:
        """Create and email a one-use verification code without revealing account existence."""
        with SessionLocal() as session:
            user = UserRepository(session).get_by_email(email)
            if not user or not user.active:
                return
            _, raw_code = PasswordResetRepository(session).create(
                user.id,
                expires_minutes=settings.password_reset_exp_minutes,
            )
            session.commit()
            recipient = user.email

        try:
            self.email_service.send_password_reset(
                recipient=recipient,
                code=raw_code,
                expires_minutes=settings.password_reset_exp_minutes,
            )
        except Exception:
            # Preserve the same public response for known and unknown emails.
            logger.exception("password_reset_email_failed", extra={"recipient": recipient})

    def _get_valid_reset(self, session, email: str, code: str):
        """Return the active reset row for (email, code) or raise 400."""
        invalid = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code invalide ou expiré",
        )
        user = UserRepository(session).get_by_email(email)
        if not user or not user.active:
            raise invalid
        self._set_auth_lookup(session, "app.current_org_id", user.org_id)

        reset_repo = PasswordResetRepository(session)
        reset = reset_repo.get_active_for_user(user.id)
        if not reset:
            raise invalid

        expires_at = reset.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            raise invalid

        if reset.token_hash != hash_reset_token(code.strip()):
            reset_repo.register_failed_attempt(reset)
            session.commit()
            raise invalid

        return user, reset

    def verify_reset_code(self, email: str, code: str) -> None:
        with SessionLocal() as session:
            self._get_valid_reset(session, email, code)

    def reset_password(self, email: str, code: str, new_password: str) -> None:
        with SessionLocal() as session:
            user, reset = self._get_valid_reset(session, email, code)
            UserRepository(session).update_password(user, hash_password(new_password))
            PasswordResetRepository(session).mark_used(reset)
            session.commit()
            user_id = user.id

        self._sessions.revoke_all_for_user(user_id, user.org_id)

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
        from app.repositories.invitation_repository import InvitationRepository
        from app.repositories.oauth_identity_repository import OAuthIdentityRepository
        from app.services.role_permissions import permissions_for_role

        email = email.lower().strip()
        if not email or not subject:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Profil OAuth incomplet")

        with SessionLocal() as session:
            self._set_auth_lookup(session, "app.auth_email", email)
            self._set_auth_lookup(session, "app.auth_oauth_subject", f"{provider}:{subject}")
            oauth_repo = OAuthIdentityRepository(session)
            user_repo = UserRepository(session)
            identity = oauth_repo.get_by_provider_subject(provider, subject)
            user: UserModel | None = None
            if identity:
                user = user_repo.get_by_id(identity.user_id)
            if not user:
                user = user_repo.get_by_email(email)
            if not user:
                # Unknown identities may join only the organization named by a valid invitation.
                invitation = InvitationRepository(session).get_pending_by_email_any_org(email)
                now = datetime.now(timezone.utc)
                invitation_expiry = invitation.expires_at if invitation else None
                if invitation_expiry and invitation_expiry.tzinfo is None:
                    invitation_expiry = invitation_expiry.replace(tzinfo=timezone.utc)
                if not invitation or invitation_expiry is None or invitation_expiry <= now:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="OAUTH_ONBOARDING_REQUIRED",
                    )
                self._set_auth_lookup(session, "app.current_org_id", invitation.org_id)
                user = user_repo.create(
                    org_id=invitation.org_id,
                    email=email,
                    first_name=first_name or "OAuth",
                    last_name=last_name or provider.title(),
                    role=invitation.role,
                    permissions=permissions_for_role(invitation.role),
                    password_hash=hash_password(secrets.token_urlsafe(24)),
                )
                invitation.status = "accepted"
                invitation.accepted_at = now
            if not user.active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

            self._set_auth_lookup(session, "app.current_org_id", user.org_id)
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

    def _issue_tokens(
        self,
        user: UserModel,
        *,
        family_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, str]:
        if self._sessions.count_active_for_user(user.id, user.org_id) >= settings.max_refresh_sessions_per_user:
            self._sessions.revoke_all_for_user(user.id, user.org_id)

        session_id = secrets.token_hex(16)
        family_id = family_id or secrets.token_hex(16)
        refresh = create_refresh_token(user.id, session_id)
        self._sessions.save(
            RefreshSession(
                session_id=session_id,
                org_id=user.org_id,
                user_id=user.id,
                family_id=family_id,
                token_hash=hash_refresh_token(refresh),
                created_at=datetime.now(tz=timezone.utc),
                expires_at=datetime.now(tz=timezone.utc) + timedelta(days=settings.refresh_token_exp_days),
                ip_address=ip_address,
                user_agent=(user_agent or "")[:512] or None,
            )
        )
        access = create_access_token(user.id, self._claims_for_user(user))
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

        if not session or session.user_id != user_id or session.token_hash != hash_refresh_token(refresh_token):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide")
        if session.revoked:
            self._sessions.revoke_family(session.family_id, session.org_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Réutilisation de refresh token détectée")
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at <= datetime.now(timezone.utc):
            self._sessions.revoke(session_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expirée")

        user = self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

        access, refresh = self._issue_tokens(user, family_id=session.family_id)
        new_session_id = str(decode_token(refresh).get("sid") or "")
        self._sessions.revoke(session_id, replaced_by_id=new_session_id)
        return access, refresh

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except Exception:
            return
        if payload.get("token_type") == "refresh" and payload.get("sid"):
            self._sessions.revoke(str(payload["sid"]))

    def logout_all(self, claims: dict[str, Any]) -> None:
        self._sessions.revoke_all_for_user(
            str(claims.get("sub") or ""),
            str(claims.get("org_id") or ""),
        )

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
