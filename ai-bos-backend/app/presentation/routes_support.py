from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_permission
from app.presentation.schemas import TicketMessageCreateBody, TicketStatusUpdateBody
from app.presentation.serializers import ticket_to_dict
from app.repositories.ticket_repository import TicketRepository
from app.services.audit_service import record_audit

VALID_STATUSES = {"open", "pending", "resolved", "closed"}


def build_support_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/support", tags=["support"])

    @router.get("/tickets")
    def list_tickets(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("support.ticket.read")),
    ) -> list[dict]:
        tickets = TicketRepository(db).list_by_org(claims_org_id(claims))
        return [ticket_to_dict(ticket) for ticket in tickets]

    @router.get("/tickets/{ticket_id}")
    def get_ticket(
        ticket_id: str,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("support.ticket.read")),
    ) -> dict:
        ticket = TicketRepository(db).get_by_id(claims_org_id(claims), ticket_id)
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket introuvable")
        return ticket_to_dict(ticket)

    @router.post("/tickets/{ticket_id}/messages", status_code=status.HTTP_201_CREATED)
    def reply_to_ticket(
        ticket_id: str,
        body: TicketMessageCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("support.ticket.write")),
    ) -> dict:
        org_id = claims_org_id(claims)
        repo = TicketRepository(db)
        ticket = repo.get_by_id(org_id, ticket_id)
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket introuvable")

        author = body.author or f"{claims.get('first_name', '')} {claims.get('last_name', '')}".strip() or "Support Agent"
        repo.add_message(
            ticket,
            org_id=org_id,
            author=author,
            content=body.content.strip(),
            is_internal=body.isInternal,
        )
        record_audit(
            db,
            claims,
            action="UPDATE",
            resource="Ticket",
            resource_id=ticket.id,
            details="internal_note" if body.isInternal else "reply",
            request=request,
        )
        db.commit()
        db.refresh(ticket)
        return ticket_to_dict(ticket)

    @router.patch("/tickets/{ticket_id}/status")
    def update_ticket_status(
        ticket_id: str,
        body: TicketStatusUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("support.ticket.write")),
    ) -> dict:
        if body.status not in VALID_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = TicketRepository(db)
        ticket = repo.get_by_id(claims_org_id(claims), ticket_id)
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket introuvable")
        repo.update_status(ticket, body.status)
        record_audit(db, claims, action="UPDATE", resource="Ticket", resource_id=ticket.id, details=f"status={body.status}", request=request)
        db.commit()
        db.refresh(ticket)
        return ticket_to_dict(ticket)

    return router
