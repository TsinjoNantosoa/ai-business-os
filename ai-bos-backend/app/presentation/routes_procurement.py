from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, claims_user_id, require_auth, require_permission
from app.presentation.schemas import (
    PurchaseOrderCreateBody,
    PurchaseOrderUpdateBody,
    SupplierCreateBody,
    SupplierUpdateBody,
)
from app.repositories.catalog_repository import (
    PurchaseOrderRepository,
    SupplierRepository,
    purchase_order_to_dict,
    supplier_to_dict,
)
from app.repositories.user_repository import UserRepository
from app.services.audit_service import record_audit

SUPPLIER_STATUSES = {"active", "inactive", "blocked"}
PO_STATUSES = {"draft", "submitted", "approved", "ordered", "received", "cancelled"}


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def build_procurement_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/procurement", tags=["procurement"])

    @router.get("/suppliers")
    def suppliers(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        rows = SupplierRepository(db).list_by_org(claims_org_id(claims))
        return [supplier_to_dict(s) for s in rows]

    @router.post("/suppliers", status_code=status.HTTP_201_CREATED)
    def create_supplier(
        body: SupplierCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("inventory.write")),
    ) -> dict:
        if body.status not in SUPPLIER_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        supplier = SupplierRepository(db).create(
            claims_org_id(claims),
            name=body.name.strip(),
            email=body.email.strip().lower(),
            phone=body.phone,
            rating=body.rating,
            country=body.country.strip(),
            status=body.status,
        )
        record_audit(db, claims, action="CREATE", resource="Supplier", resource_id=supplier.id, details=supplier.name, request=request)
        db.commit()
        db.refresh(supplier)
        return supplier_to_dict(supplier)

    @router.patch("/suppliers/{supplier_id}")
    def update_supplier(
        supplier_id: str,
        body: SupplierUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("inventory.write")),
    ) -> dict:
        if body.status is not None and body.status not in SUPPLIER_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = SupplierRepository(db)
        supplier = repo.get_by_id(claims_org_id(claims), supplier_id)
        if not supplier:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fournisseur introuvable")
        repo.update(
            supplier,
            name=body.name.strip() if body.name else None,
            email=body.email.strip().lower() if body.email else None,
            phone=body.phone,
            rating=body.rating,
            country=body.country.strip() if body.country else None,
            status=body.status,
        )
        record_audit(db, claims, action="UPDATE", resource="Supplier", resource_id=supplier.id, details=supplier.name, request=request)
        db.commit()
        db.refresh(supplier)
        return supplier_to_dict(supplier)

    @router.get("/purchase-orders")
    def purchase_orders(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        rows = PurchaseOrderRepository(db).list_by_org(claims_org_id(claims))
        return [purchase_order_to_dict(po) for po in rows]

    @router.post("/purchase-orders", status_code=status.HTTP_201_CREATED)
    def create_purchase_order(
        body: PurchaseOrderCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("inventory.write")),
    ) -> dict:
        if body.status not in PO_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        org_id = claims_org_id(claims)
        repo = PurchaseOrderRepository(db)
        user = UserRepository(db).get_by_id(claims_user_id(claims))
        owner = f"{user.first_name} {user.last_name}".strip() if user else "—"
        supplier_name = body.supplierName.strip()
        if body.supplierId:
            supplier = SupplierRepository(db).get_by_id(org_id, body.supplierId)
            if supplier:
                supplier_name = supplier.name
        po = repo.create(
            org_id,
            po_number=repo.next_po_number(org_id),
            supplier_id=body.supplierId,
            supplier_name=supplier_name,
            status=body.status,
            total_amount=body.totalAmount,
            currency=body.currency,
            created_at_iso=_today(),
            expected_at=body.expectedAt or _today(),
            owner_name=owner,
            item_count=body.itemCount,
        )
        record_audit(db, claims, action="CREATE", resource="PurchaseOrder", resource_id=po.id, details=po.po_number, request=request)
        db.commit()
        db.refresh(po)
        return purchase_order_to_dict(po)

    @router.patch("/purchase-orders/{po_id}")
    def update_purchase_order(
        po_id: str,
        body: PurchaseOrderUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("inventory.write")),
    ) -> dict:
        if body.status is not None and body.status not in PO_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = PurchaseOrderRepository(db)
        po = repo.get_by_id(claims_org_id(claims), po_id)
        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande introuvable")
        repo.update(
            po,
            supplier_id=body.supplierId,
            supplier_name=body.supplierName.strip() if body.supplierName else None,
            status=body.status,
            total_amount=body.totalAmount,
            currency=body.currency,
            expected_at=body.expectedAt,
            item_count=body.itemCount,
        )
        record_audit(db, claims, action="UPDATE", resource="PurchaseOrder", resource_id=po.id, details=po.po_number, request=request)
        db.commit()
        db.refresh(po)
        return purchase_order_to_dict(po)

    return router
