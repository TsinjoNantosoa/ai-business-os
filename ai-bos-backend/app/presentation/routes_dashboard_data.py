from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import require_auth


def build_dashboard_data_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["dashboard-data"])

    @router.get("/finance/overview")
    def finance_overview(_claims: dict = Depends(require_auth)) -> dict:
        return {
            "cashBalance": 128400,
            "arOutstanding": 45200,
            "apOutstanding": 18600,
            "burnRate": 12400,
            "monthlyRevenue": [
                {"month": "Jan", "revenue": 210000, "expenses": 122000},
                {"month": "Feb", "revenue": 230000, "expenses": 130000},
                {"month": "Mar", "revenue": 250000, "expenses": 138000},
                {"month": "Apr", "revenue": 240000, "expenses": 132000},
                {"month": "May", "revenue": 260000, "expenses": 140000},
            ],
            "agingReceivables": [
                {"bucket": "0-30d", "amount": 18400},
                {"bucket": "31-60d", "amount": 13800},
                {"bucket": "61-90d", "amount": 8200},
                {"bucket": "90+d", "amount": 5400},
            ],
            "recentTransactions": [
                {
                    "id": "tx-1",
                    "description": "Facture #INV-1021",
                    "amount": 12400,
                    "type": "income",
                    "category": "Invoices",
                    "date": "2026-07-01",
                    "account": "Main AR",
                },
                {
                    "id": "tx-2",
                    "description": "Dépense SaaS",
                    "amount": 2400,
                    "type": "expense",
                    "category": "Subscriptions",
                    "date": "2026-06-28",
                    "account": "Operating",
                },
            ],
        }

    @router.get("/hr/employees")
    def employees(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "e-1",
                "firstName": "Aina",
                "lastName": "CEO",
                "email": "ceo@demo.aibos.io",
                "phone": "+33 6 00 00 00 01",
                "position": "Chief Executive Officer",
                "department": "Management",
                "startDate": "2026-01-10",
                "status": "active",
                "avatarColor": "bg-primary-100",
                "salary": 140000,
                "location": "Paris",
            },
            {
                "id": "e-2",
                "firstName": "Demo",
                "lastName": "Staff",
                "email": "staff@demo.aibos.io",
                "position": "Staff",
                "department": "Operations",
                "startDate": "2026-02-01",
                "status": "active",
                "avatarColor": "bg-slate-100",
                "salary": 65000,
                "location": "Lyon",
            },
        ]

    return router

