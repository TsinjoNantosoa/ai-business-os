from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_auth, require_permission
from app.presentation.schemas import InvoiceCreateBody, TransactionCreateBody, TransactionUpdateBody
from app.presentation.serializers import finance_invoice_to_dict, parse_iso_datetime
from app.repositories.catalog_repository import FinanceTransactionRepository, transaction_to_dict
from app.repositories.invoice_repository import InvoiceRepository
from app.services.audit_service import record_audit

TX_TYPES = {"income", "expense"}


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
        from app.services.event_bus import EventBus

        EventBus(db).publish(
            org_id=claims_org_id(claims),
            event_type="finance.invoice.created",
            payload={
                "invoiceId": invoice.id,
                "invoiceNumber": invoice.invoice_number,
                "clientName": invoice.client_name,
                "totalAmount": invoice.total_amount,
            },
            source="finance",
        )
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
    def transactions(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        rows = FinanceTransactionRepository(db).list_by_org(claims_org_id(claims))
        return [transaction_to_dict(tx) for tx in rows]

    @router.post("/transactions", status_code=status.HTTP_201_CREATED)
    def create_transaction(
        body: TransactionCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("finance.payment.write")),
    ) -> dict:
        if body.type not in TX_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")
        from datetime import datetime, timezone

        tx = FinanceTransactionRepository(db).create(
            claims_org_id(claims),
            description=body.description.strip(),
            amount=body.amount,
            type=body.type,
            category=body.category.strip(),
            date=body.date or datetime.now(timezone.utc).date().isoformat(),
            account=body.account.strip(),
        )
        record_audit(db, claims, action="CREATE", resource="FinanceTransaction", resource_id=tx.id, details=tx.description, request=request)
        db.commit()
        db.refresh(tx)
        return transaction_to_dict(tx)

    @router.patch("/transactions/{tx_id}")
    def update_transaction(
        tx_id: str,
        body: TransactionUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("finance.payment.write")),
    ) -> dict:
        if body.type is not None and body.type not in TX_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")
        repo = FinanceTransactionRepository(db)
        tx = repo.get_by_id(claims_org_id(claims), tx_id)
        if not tx:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction introuvable")
        repo.update(
            tx,
            description=body.description.strip() if body.description else None,
            amount=body.amount,
            type=body.type,
            category=body.category.strip() if body.category else None,
            date=body.date,
            account=body.account.strip() if body.account else None,
        )
        record_audit(db, claims, action="UPDATE", resource="FinanceTransaction", resource_id=tx.id, details=tx.description, request=request)
        db.commit()
        db.refresh(tx)
        return transaction_to_dict(tx)

    return router
