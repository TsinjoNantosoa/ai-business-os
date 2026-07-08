from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import require_auth


def build_finance_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/finance", tags=["finance"])

    @router.get("/invoices")
    def invoices(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "inv-1",
                "invoiceNumber": "INV-1021",
                "clientId": "cust-1",
                "clientName": "Acme Corp",
                "amount": 10000,
                "taxAmount": 2000,
                "totalAmount": 12000,
                "currency": "EUR",
                "status": "paid",
                "issueDate": "2026-06-20",
                "dueDate": "2026-07-05",
                "paidDate": "2026-07-02",
                "lineItems": [
                    {
                        "id": "li-inv-1",
                        "description": "Licence AI Copilot",
                        "quantity": 1,
                        "unitPrice": 10000,
                        "taxRate": 0.2,
                        "total": 12000,
                    }
                ],
            },
            {
                "id": "inv-2",
                "invoiceNumber": "INV-1044",
                "clientId": "cust-2",
                "clientName": "Globex",
                "amount": 22000,
                "taxAmount": 4400,
                "totalAmount": 26400,
                "currency": "EUR",
                "status": "overdue",
                "issueDate": "2026-05-25",
                "dueDate": "2026-06-25",
                "lineItems": [
                    {
                        "id": "li-inv-2",
                        "description": "Abonnement & Support",
                        "quantity": 1,
                        "unitPrice": 22000,
                        "taxRate": 0.2,
                        "total": 26400,
                    }
                ],
            },
        ]

    @router.get("/transactions")
    def transactions(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "tx-10",
                "description": "Paiement facture INV-1021",
                "amount": 12000,
                "type": "income",
                "category": "Invoices",
                "date": "2026-07-02",
                "account": "Main AR",
            },
            {
                "id": "tx-11",
                "description": "Dépense marketing — Ads",
                "amount": 3400,
                "type": "expense",
                "category": "Marketing ads",
                "date": "2026-06-28",
                "account": "Operating",
            },
            {
                "id": "tx-12",
                "description": "Achat licences cloud",
                "amount": 2900,
                "type": "expense",
                "category": "Cloud",
                "date": "2026-06-26",
                "account": "Operating",
            },
        ]

    return router

