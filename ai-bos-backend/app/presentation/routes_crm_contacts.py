from __future__ import annotations

from fastapi import APIRouter, Depends

from app.presentation.deps import require_auth


def build_crm_contacts_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/crm", tags=["crm"])

    @router.get("/contacts")
    def contacts(_claims: dict = Depends(require_auth)) -> list[dict]:
        return [
            {
                "id": "c-1",
                "firstName": "Amina",
                "lastName": "Benali",
                "email": "amina@acme.example",
                "phone": "+33 6 11 22 33 44",
                "company": "Acme Corp",
                "position": "Directrice Marketing",
                "status": "active",
                "ownerId": "u-owner-1",
                "ownerName": "Aina CEO",
                "tags": ["renewal", "enterprise"],
                "lastActivityAt": "2026-07-01",
                "createdAt": "2026-02-01",
                "avatarColor": "bg-primary-100",
            },
            {
                "id": "c-2",
                "firstName": "Karim",
                "lastName": "Diallo",
                "email": "karim@globex.example",
                "phone": "+33 6 55 66 77 88",
                "company": "Globex",
                "position": "Responsable IT",
                "status": "lead",
                "ownerId": "u-owner-1",
                "ownerName": "Aina CEO",
                "tags": ["lead", "priority"],
                "lastActivityAt": "2026-06-27",
                "createdAt": "2026-05-20",
                "avatarColor": "bg-emerald-100",
            },
        ]

    return router

