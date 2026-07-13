from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, claims_user_id, require_auth, require_permission
from app.presentation.schemas import ContactCreateBody, ContactUpdateBody
from app.presentation.serializers import contact_to_dict
from app.repositories.contact_repository import ContactRepository
from app.services.audit_service import record_audit
from app.services.notification_service import create_and_publish_notification


def build_crm_contacts_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/crm", tags=["crm"])

    @router.get("/contacts")
    def list_contacts(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("crm.contact.read")),
    ) -> list[dict]:
        org_id = claims_org_id(claims)
        contacts = ContactRepository(db).list_by_org(org_id)
        return [contact_to_dict(contact) for contact in contacts]

    @router.post("/contacts", status_code=status.HTTP_201_CREATED)
    def create_contact(
        body: ContactCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("crm.contact.write")),
    ) -> dict:
        org_id = claims_org_id(claims)
        owner_id = claims_user_id(claims)
        owner_name = f"{claims.get('first_name', '')} {claims.get('last_name', '')}".strip() or None

        contact = ContactRepository(db).create(
            org_id=org_id,
            first_name=body.firstName,
            last_name=body.lastName,
            email=body.email,
            company=body.company,
            owner_id=owner_id,
            owner_name=owner_name,
            phone=body.phone,
            position=body.position,
            status=body.status,
            tags=body.tags,
        )
        record_audit(db, claims, action="CREATE", resource="Contact", resource_id=contact.id, details=contact.email, request=request)
        create_and_publish_notification(
            db,
            org_id=org_id,
            type="info",
            title="Nouveau contact",
            message=f"{contact.first_name} {contact.last_name} ({contact.email}) a été ajouté",
            link="/app/crm/contacts",
        )
        db.commit()
        db.refresh(contact)
        return contact_to_dict(contact)

    @router.patch("/contacts/{contact_id}")
    def update_contact(
        contact_id: str,
        body: ContactUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("crm.contact.write")),
    ) -> dict:
        repo = ContactRepository(db)
        contact = repo.get_by_id(claims_org_id(claims), contact_id)
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact introuvable")

        updates = {
            "first_name": body.firstName,
            "last_name": body.lastName,
            "email": body.email.lower().strip() if body.email else None,
            "company": body.company,
            "phone": body.phone,
            "position": body.position,
            "status": body.status,
            "tags": body.tags,
        }
        repo.update(contact, **{k: v for k, v in updates.items() if v is not None})
        record_audit(db, claims, action="UPDATE", resource="Contact", resource_id=contact.id, request=request)
        db.commit()
        db.refresh(contact)
        return contact_to_dict(contact)

    @router.delete("/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_contact(
        contact_id: str,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("crm.contact.write")),
    ) -> None:
        repo = ContactRepository(db)
        contact = repo.get_by_id(claims_org_id(claims), contact_id)
        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact introuvable")
        record_audit(db, claims, action="DELETE", resource="Contact", resource_id=contact.id, request=request)
        repo.delete(contact)
        db.commit()

    return router
