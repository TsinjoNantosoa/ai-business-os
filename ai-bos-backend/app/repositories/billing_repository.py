from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.billing import BillingInvoice, BillingPlan, Subscription


class BillingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_plans(self) -> list[BillingPlan]:
        return list(self._session.scalars(select(BillingPlan).order_by(BillingPlan.price_monthly)).all())

    def get_plan_by_code(self, code: str) -> BillingPlan | None:
        return self._session.scalars(select(BillingPlan).where(BillingPlan.code == code)).first()

    def get_plan_by_id(self, plan_id: str) -> BillingPlan | None:
        return self._session.get(BillingPlan, plan_id)

    def plans_count(self) -> int:
        return len(self.list_plans())

    def get_subscription_for_org(self, org_id: str) -> Subscription | None:
        stmt = (
            select(Subscription)
            .options(joinedload(Subscription.plan))
            .where(Subscription.org_id == org_id)
            .order_by(Subscription.created_at.desc())
        )
        return self._session.scalars(stmt).first()

    def list_invoices_for_org(self, org_id: str) -> list[BillingInvoice]:
        stmt = (
            select(BillingInvoice)
            .where(BillingInvoice.org_id == org_id)
            .order_by(BillingInvoice.created_at.desc())
        )
        return list(self._session.scalars(stmt).all())

    def create_subscription(
        self,
        *,
        subscription_id: str,
        org_id: str,
        plan_id: str,
        status: str,
        period_start: datetime,
        period_end: datetime,
        seats_used: int,
        ai_tokens_used: int,
        storage_gb_used: int,
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
    ) -> Subscription:
        sub = Subscription(
            id=subscription_id,
            org_id=org_id,
            plan_id=plan_id,
            status=status,
            current_period_start=period_start,
            current_period_end=period_end,
            seats_used=seats_used,
            ai_tokens_used=ai_tokens_used,
            storage_gb_used=storage_gb_used,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
        )
        self._session.add(sub)
        return sub

    def update_subscription_plan(self, subscription: Subscription, plan_id: str) -> Subscription:
        subscription.plan_id = plan_id
        subscription.updated_at = datetime.now(timezone.utc)
        return subscription

    def mark_invoice_paid(self, stripe_invoice_id: str) -> BillingInvoice | None:
        invoice = self._session.scalars(
            select(BillingInvoice).where(BillingInvoice.stripe_invoice_id == stripe_invoice_id)
        ).first()
        if invoice:
            invoice.status = "paid"
        return invoice
