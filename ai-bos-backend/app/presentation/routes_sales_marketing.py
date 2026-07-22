from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, claims_user_id, require_auth, require_permission
from app.presentation.schemas import (
    CampaignCreateBody,
    CampaignUpdateBody,
    OrderCreateBody,
    OrderUpdateBody,
)
from app.presentation.serializers import campaign_to_dict, sales_order_to_dict
from app.repositories.ops_repository import CampaignRepository, SalesOrderRepository
from app.repositories.user_repository import UserRepository
from app.services.audit_service import record_audit

ORDER_STATUSES = {"draft", "sent", "accepted", "fulfilled", "invoiced", "cancelled"}
CAMPAIGN_TYPES = {"email", "social", "ads", "webinar", "content", "sms"}
CAMPAIGN_STATUSES = {"draft", "scheduled", "active", "paused", "completed"}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def build_sales_marketing_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["sales-marketing"])

    # --- Sales orders ---

    @router.get("/sales/orders")
    def orders(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        items = SalesOrderRepository(db).list_by_org(claims_org_id(claims))
        return [sales_order_to_dict(order) for order in items]

    @router.post("/sales/orders", status_code=status.HTTP_201_CREATED)
    def create_order(
        body: OrderCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("sales.order.write")),
    ) -> dict:
        if body.status not in ORDER_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")

        org_id = claims_org_id(claims)
        repo = SalesOrderRepository(db)

        line_items = []
        amount = 0.0
        for index, item in enumerate(body.lineItems):
            total = item.quantity * item.unitPrice
            amount += total
            line_items.append(
                {
                    "id": f"li-{index + 1}",
                    "description": item.description,
                    "quantity": item.quantity,
                    "unitPrice": item.unitPrice,
                    "total": total,
                }
            )

        user = UserRepository(db).get_by_id(claims_user_id(claims))
        rep_name = f"{user.first_name} {user.last_name}".strip() if user else None

        order = repo.create(
            org_id,
            order_number=repo.next_order_number(org_id),
            customer_id=body.customerId,
            customer_name=body.customerName.strip(),
            status=body.status,
            amount=amount,
            currency=body.currency,
            date=body.date or _today(),
            sales_rep_id=claims_user_id(claims),
            sales_rep_name=rep_name,
            line_items=line_items,
        )
        record_audit(db, claims, action="CREATE", resource="SalesOrder", resource_id=order.id, details=order.order_number, request=request)
        db.commit()
        db.refresh(order)
        return sales_order_to_dict(order)

    @router.patch("/sales/orders/{order_id}")
    def update_order(
        order_id: str,
        body: OrderUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("sales.order.write")),
    ) -> dict:
        if body.status is not None and body.status not in ORDER_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = SalesOrderRepository(db)
        order = repo.get_by_id(claims_org_id(claims), order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande introuvable")

        fields: dict = {
            "customer_name": body.customerName,
            "status": body.status,
        }
        if body.lineItems is not None:
            line_items = []
            amount = 0.0
            for index, item in enumerate(body.lineItems):
                total = item.quantity * item.unitPrice
                amount += total
                line_items.append(
                    {
                        "id": f"li-{index + 1}",
                        "description": item.description,
                        "quantity": item.quantity,
                        "unitPrice": item.unitPrice,
                        "total": total,
                    }
                )
            fields["line_items"] = line_items
            fields["amount"] = amount

        repo.update(order, **fields)
        record_audit(db, claims, action="UPDATE", resource="SalesOrder", resource_id=order.id, details=f"status={body.status}", request=request)
        db.commit()
        db.refresh(order)
        return sales_order_to_dict(order)

    # --- Marketing campaigns ---

    @router.get("/marketing/campaigns")
    def campaigns(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        items = CampaignRepository(db).list_by_org(claims_org_id(claims))
        return [campaign_to_dict(campaign) for campaign in items]

    @router.post("/marketing/campaigns", status_code=status.HTTP_201_CREATED)
    def create_campaign(
        body: CampaignCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("marketing.campaign.write")),
    ) -> dict:
        if body.type not in CAMPAIGN_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")
        if body.status not in CAMPAIGN_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")

        campaign = CampaignRepository(db).create(
            claims_org_id(claims),
            name=body.name.strip(),
            type=body.type,
            status=body.status,
            reach=0,
            open_rate=0,
            click_rate=0,
            conversions=0,
            budget=body.budget,
            spent=0,
            start_date=body.startDate or _today(),
            end_date=body.endDate,
        )
        record_audit(db, claims, action="CREATE", resource="Campaign", resource_id=campaign.id, details=campaign.name, request=request)
        db.commit()
        db.refresh(campaign)
        return campaign_to_dict(campaign)

    @router.patch("/marketing/campaigns/{campaign_id}")
    def update_campaign(
        campaign_id: str,
        body: CampaignUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("marketing.campaign.write")),
    ) -> dict:
        if body.type is not None and body.type not in CAMPAIGN_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type invalide")
        if body.status is not None and body.status not in CAMPAIGN_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = CampaignRepository(db)
        campaign = repo.get_by_id(claims_org_id(claims), campaign_id)
        if not campaign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campagne introuvable")

        repo.update(
            campaign,
            name=body.name,
            type=body.type,
            status=body.status,
            budget=body.budget,
            spent=body.spent,
            start_date=body.startDate,
            end_date=body.endDate,
        )
        record_audit(db, claims, action="UPDATE", resource="Campaign", resource_id=campaign.id, details=f"status={body.status}", request=request)
        db.commit()
        db.refresh(campaign)
        return campaign_to_dict(campaign)

    return router
