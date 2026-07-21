from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data.seed_ops import DEMO_TRANSACTIONS
from app.presentation.deps import claims_org_id, require_auth, require_permission
from app.presentation.schemas import InvoiceCreateBody
from app.presentation.serializers import finance_invoice_to_dict, parse_iso_datetime
from app.repositories.invoice_repository import InvoiceRepository
from app.services.audit_service import record_audit


def build_finance_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/finance", tags=["finance"])

    @router.get("/invoices")
    def list_invoices(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("finance.invoice.read")),
    ) -> list[dict]:
        invoices = InvoiceRepository(db).list_by_org(claims_org_id(claims))
        return [finance_invoice_to_dict(invoice) for invoice in invoices]

    @router.post("/invoices", status_code=status.HTTP_201_CREATED)
    def create_invoice(
        body: InvoiceCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("finance.invoice.write")),
    ) -> dict:
        line_items = []
        for index, item in enumerate(body.lineItems, start=1):
            total = item.quantity * item.unitPrice
            line_items.append(
                {
                    "id": f"li-new-{index}",
                    "description": item.description,
                    "quantity": item.quantity,
                    "unitPrice": item.unitPrice,
                    "taxRate": item.taxRate,
                    "total": total,
                }
            )

        now = parse_iso_datetime(body.issueDate) if body.issueDate else None
        due = parse_iso_datetime(body.dueDate) if body.dueDate else None
        if now and not due:
            due = now + timedelta(days=30)

        invoice = InvoiceRepository(db).create(
            org_id=claims_org_id(claims),
            client_id=body.clientId,
            client_name=body.clientName,
            line_items=line_items,
            currency=body.currency,
            issue_date=now,
            due_date=due,
        )
        record_audit(db, claims, action="CREATE", resource="Invoice", resource_id=invoice.id, details=invoice.invoice_number, request=request)
        db.commit()
        db.refresh(invoice)
        return finance_invoice_to_dict(invoice)

    @router.post("/invoices/{invoice_id}/send")
    def send_invoice(
        invoice_id: str,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("finance.invoice.write")),
    ) -> dict:
        repo = InvoiceRepository(db)
        invoice = repo.get_by_id(claims_org_id(claims), invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Facture introuvable")
        if invoice.status != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seules les factures brouillon peuvent être envoyées")
        repo.mark_sent(invoice)
        record_audit(db, claims, action="UPDATE", resource="Invoice", resource_id=invoice.id, details="send", request=request)
        db.commit()
        db.refresh(invoice)
        return finance_invoice_to_dict(invoice)

    @router.get("/transactions")
    def transactions(_claims: dict = Depends(require_auth)) -> list[dict]:
        return DEMO_TRANSACTIONS

    return router
