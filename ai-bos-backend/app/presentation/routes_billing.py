from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.billing import Subscription
from app.presentation.deps import claims_org_id, require_permission
from app.presentation.schemas import CheckoutBody
from app.presentation.serializers import billing_invoice_to_dict, plan_to_dict, subscription_to_dict
from app.repositories.billing_repository import BillingRepository
from app.services.stripe_service import StripeService


def build_billing_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
    stripe_service = StripeService()

    @router.get("/plans")
    def list_plans(
        db: Session = Depends(get_db),
        _claims: dict = Depends(require_permission("settings.billing")),
    ) -> list[dict]:
        return [plan_to_dict(plan) for plan in BillingRepository(db).list_plans()]

    @router.get("/subscription")
    def get_subscription(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.billing")),
    ) -> dict:
        subscription = BillingRepository(db).get_subscription_for_org(claims_org_id(claims))
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Abonnement introuvable")
        return subscription_to_dict(subscription)

    @router.get("/overview")
    def billing_overview(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.billing")),
    ) -> dict:
        org_id = claims_org_id(claims)
        repo = BillingRepository(db)
        subscription = repo.get_subscription_for_org(org_id)
        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Abonnement introuvable")
        return {
            "subscription": subscription_to_dict(subscription),
            "invoices": [billing_invoice_to_dict(inv) for inv in repo.list_invoices_for_org(org_id)],
        }

    @router.get("/invoices")
    def list_invoices(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.billing")),
    ) -> list[dict]:
        invoices = BillingRepository(db).list_invoices_for_org(claims_org_id(claims))
        return [billing_invoice_to_dict(inv) for inv in invoices]

    @router.post("/checkout")
    def create_checkout(
        body: CheckoutBody,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("settings.billing")),
    ) -> dict[str, str]:
        plan = BillingRepository(db).get_plan_by_code(body.planCode)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan introuvable")

        return stripe_service.create_checkout_session(
            org_id=claims_org_id(claims),
            plan_code=plan.code,
            customer_email=str(claims.get("email") or "ceo@demo.aibos.io"),
            price_amount=plan.price_monthly,
            currency=plan.currency,
            stripe_price_id=plan.stripe_price_id,
        )

    @router.post("/webhooks/stripe", status_code=status.HTTP_200_OK)
    async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict[str, str]:
        payload = await request.body()
        signature = request.headers.get("Stripe-Signature")
        try:
            event = stripe_service.verify_webhook(payload, signature)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook invalide") from exc

        repo = BillingRepository(db)
        event_type = event.get("type", "")
        data_object = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            org_id = data_object.get("metadata", {}).get("org_id")
            plan_code = data_object.get("metadata", {}).get("plan_code")
            plan = repo.get_plan_by_code(plan_code) if plan_code else None
            subscription = repo.get_subscription_for_org(org_id) if org_id else None
            if plan and subscription:
                repo.update_subscription_plan(subscription, plan.id)
                subscription.status = "active"
                subscription.stripe_customer_id = data_object.get("customer")
                subscription.stripe_subscription_id = data_object.get("subscription")
                db.commit()

        elif event_type == "invoice.paid":
            stripe_invoice_id = data_object.get("id")
            if stripe_invoice_id and repo.mark_invoice_paid(stripe_invoice_id):
                db.commit()

        elif event_type == "customer.subscription.updated":
            stripe_sub_id = data_object.get("id")
            status_value = data_object.get("status", "active")
            sub = db.scalars(
                select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
            ).first()
            if sub:
                sub.status = status_value
                db.commit()

        return {"received": "true"}

    return router
