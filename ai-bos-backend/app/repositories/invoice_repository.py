from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finance_invoice import FinanceInvoice


class InvoiceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[FinanceInvoice]:
        stmt = (
            select(FinanceInvoice)
            .where(FinanceInvoice.org_id == org_id)
            .order_by(FinanceInvoice.issue_date.desc())
        )
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, invoice_id: str) -> FinanceInvoice | None:
        stmt = select(FinanceInvoice).where(
            FinanceInvoice.org_id == org_id,
            FinanceInvoice.id == invoice_id,
        )
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(FinanceInvoice)).all()))

    def _next_invoice_number(self, org_id: str) -> str:
        existing = self.list_by_org(org_id)
        max_num = 0
        for invoice in existing:
            suffix = invoice.invoice_number.rsplit("-", 1)[-1]
            if suffix.isdigit():
                max_num = max(max_num, int(suffix))
        return f"INV-2024-{max_num + 1:03d}"

    def create(
        self,
        *,
        org_id: str,
        client_id: str,
        client_name: str,
        line_items: list[dict],
        currency: str = "EUR",
        issue_date: datetime | None = None,
        due_date: datetime | None = None,
    ) -> FinanceInvoice:
        now = datetime.now(timezone.utc)
        issue_date = issue_date or now
        due_date = due_date or (issue_date + timedelta(days=30))

        amount = sum(item.get("total", 0) for item in line_items)
        tax_amount = sum(
            round(item.get("total", 0) * (item.get("taxRate", 0) / 100))
            for item in line_items
        )
        invoice = FinanceInvoice(
            id=f"inv-{secrets.token_hex(6)}",
            org_id=org_id,
            invoice_number=self._next_invoice_number(org_id),
            client_id=client_id,
            client_name=client_name,
            amount=amount,
            tax_amount=tax_amount,
            total_amount=amount + tax_amount,
            currency=currency,
            status="draft",
            issue_date=issue_date,
            due_date=due_date,
            paid_date=None,
            line_items=line_items,
            created_at=now,
            updated_at=now,
        )
        self._session.add(invoice)
        self._session.flush()
        return invoice

    def mark_sent(self, invoice: FinanceInvoice) -> FinanceInvoice:
        invoice.status = "sent"
        invoice.updated_at = datetime.now(timezone.utc)
        return invoice
