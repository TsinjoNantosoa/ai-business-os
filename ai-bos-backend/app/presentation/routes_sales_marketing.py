from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import require_auth


def build_sales_marketing_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["sales-marketing"])

    @router.get("/sales/orders")
    def orders(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "so-1",
                "orderNumber": "SO-2049",
                "customerId": "cust-1",
                "customerName": "Acme Corp",
                "status": "accepted",
                "amount": 124000,
                "currency": "EUR",
                "date": "2026-06-18",
                "salesRepId": "u-owner-1",
                "salesRepName": "Aina CEO",
                "lineItems": [
                    {
                        "id": "li-1",
                        "description": "Pack CRM + IA",
                        "quantity": 10,
                        "unitPrice": 9800,
                        "total": 98000,
                    },
                    {
                        "id": "li-2",
                        "description": "Support premium",
                        "quantity": 1,
                        "unitPrice": 26000,
                        "total": 26000,
                    },
                ],
            }
        ]

    @router.get("/marketing/campaigns")
    def campaigns(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "camp-1",
                "name": "Q3 Growth — Paid Search",
                "type": "email",
                "status": "active",
                "reach": 120000,
                "openRate": 0.32,
                "clickRate": 0.11,
                "conversions": 1460,
                "budget": 65000,
                "spent": 42000,
                "startDate": "2026-07-01",
                "endDate": "2026-09-30",
            },
            {
                "id": "camp-2",
                "name": "Webinar Partner Program",
                "type": "webinar",
                "status": "scheduled",
                "reach": 54000,
                "openRate": 0.27,
                "clickRate": 0.07,
                "conversions": 520,
                "budget": 22000,
                "spent": 0,
                "startDate": "2026-08-10",
            },
        ]

    return router

