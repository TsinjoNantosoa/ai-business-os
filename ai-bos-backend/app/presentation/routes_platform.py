from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.data import seed
from app.presentation.deps import claims_org_id, claims_user_id, require_auth, require_permission
from app.presentation.schemas import InvitationAcceptBody, InvitationCreateBody, OrganizationUpdateBody
from app.presentation.serializers import (
    audit_log_to_dict,
    invitation_to_dict,
    organization_to_dict,
    team_member_to_dict,
)
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.invitation_repository import InvitationRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import record_audit
from app.services.notification_service import create_and_publish_notification
from app.services.role_permissions import INVITABLE_ROLES, permissions_for_role


def build_platform_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/platform", tags=["platform"])

    @router.get("/organizations")
    def organizations(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        # Tenant isolation: only expose the caller's organization.
        org = OrganizationRepository(db).get_by_id(claims_org_id(claims))
        if org:
            return [organization_to_dict(org)]
        return [o for o in seed.ORGANIZATIONS if o["id"] == claims_org_id(claims)]

    @router.get("/organizations/me")
    def my_organization(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        org = OrganizationRepository(db).get_by_id(claims_org_id(claims))
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation introuvable")
        return organization_to_dict(org)

    @router.patch("/organizations/me")
    def update_my_organization(
        body: OrganizationUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.org")),
    ) -> dict:
        org_repo = OrganizationRepository(db)
        org = org_repo.get_by_id(claims_org_id(claims))
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organisation introuvable")

        updated = org_repo.update(
            org,
            name=body.name,
            currency=body.currency,
            timezone=body.timezone,
            locale=body.locale,
            address=body.address,
        )
        record_audit(
            db,
            claims,
            action="UPDATE",
            resource="Organization",
            resource_id=updated.id,
            details=updated.name,
            request=request,
        )
        return organization_to_dict(updated)

    @router.get("/team")
    def team_members(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.team")),
    ) -> list[dict]:
        users = UserRepository(db).list_by_org(claims_org_id(claims))
        return [team_member_to_dict(user) for user in users]

    @router.get("/invitations")
    def list_invitations(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.team")),
    ) -> list[dict]:
        invitations = InvitationRepository(db).list_by_org(claims_org_id(claims))
        return [invitation_to_dict(inv) for inv in invitations]

    @router.post("/invitations", status_code=status.HTTP_201_CREATED)
    def create_invitation(
        body: InvitationCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.team")),
    ) -> dict:
        org_id = claims_org_id(claims)
        role = body.role.strip().lower()
        if role not in INVITABLE_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rôle non invitable. Autorisés: {', '.join(INVITABLE_ROLES)}",
            )

        user_repo = UserRepository(db)
        if user_repo.get_by_email(body.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un utilisateur avec cet email existe déjà")

        inv_repo = InvitationRepository(db)
        if inv_repo.get_pending_by_email(org_id, body.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invitation déjà en attente pour cet email")

        invited_by_name = f"{claims.get('first_name', '')} {claims.get('last_name', '')}".strip() or "Admin"
        invitation = inv_repo.create(
            org_id=org_id,
            email=str(body.email),
            role=role,
            invited_by=claims_user_id(claims),
            invited_by_name=invited_by_name,
            message=body.message,
        )
        record_audit(
            db,
            claims,
            action="CREATE",
            resource="Invitation",
            resource_id=invitation.id,
            details=invitation.email,
            request=request,
        )
        create_and_publish_notification(
            db,
            org_id=org_id,
            type="info",
            title="Invitation envoyée",
            message=f"Invitation {invitation.role} pour {invitation.email}",
            link="/app/settings/team",
        )
        # Token returned once so UI/tests can share the invite link (email mock).
        return invitation_to_dict(invitation, include_token=True)

    @router.get("/invitations/by-token/{token}")
    def invitation_by_token(token: str, db: Session = Depends(get_db)) -> dict:
        invitation = InvitationRepository(db).get_by_token(token)
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation introuvable")

        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if invitation.status != "pending" or expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation expirée ou déjà utilisée")

        org = OrganizationRepository(db).get_by_id(invitation.org_id)
        return {
            **invitation_to_dict(invitation),
            "organizationName": org.name if org else None,
        }

    @router.post("/invitations/accept", status_code=status.HTTP_201_CREATED)
    def accept_invitation(body: InvitationAcceptBody, db: Session = Depends(get_db)) -> dict:
        inv_repo = InvitationRepository(db)
        invitation = inv_repo.get_by_token(body.token)
        if not invitation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation introuvable")

        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if invitation.status != "pending" or expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Invitation expirée ou déjà utilisée")

        user_repo = UserRepository(db)
        if user_repo.get_by_email(invitation.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un utilisateur avec cet email existe déjà")

        user = user_repo.create(
            org_id=invitation.org_id,
            email=invitation.email,
            first_name=body.firstName,
            last_name=body.lastName,
            role=invitation.role,
            permissions=permissions_for_role(invitation.role),
            password_hash=hash_password(body.password),
        )
        inv_repo.mark_accepted(invitation)
        return team_member_to_dict(user)

    @router.post("/invitations/{invitation_id}/revoke")
    def revoke_invitation(
        invitation_id: str,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.team")),
    ) -> dict:
        inv_repo = InvitationRepository(db)
        invitation = inv_repo.get_by_id(invitation_id)
        if not invitation or invitation.org_id != claims_org_id(claims):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation introuvable")
        if invitation.status != "pending":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seules les invitations en attente peuvent être révoquées")

        revoked = inv_repo.revoke(invitation)
        record_audit(
            db,
            claims,
            action="UPDATE",
            resource="Invitation",
            resource_id=revoked.id,
            details=f"revoked:{revoked.email}",
            request=request,
        )
        return invitation_to_dict(revoked)

    @router.get("/audit-logs")
    def audit_logs(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("admin.audit")),
    ) -> list[dict]:
        entries = AuditLogRepository(db).list_by_org(claims_org_id(claims), limit=100)
        return [audit_log_to_dict(entry) for entry in entries]

    return router
