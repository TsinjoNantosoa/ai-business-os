from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_auth, require_permission
from app.presentation.schemas import InventoryItemCreateBody, InventoryItemUpdateBody
from app.repositories.catalog_repository import (
    ContractRepository,
    InventoryItemRepository,
    contract_to_dict,
    inventory_to_dict,
)
from app.services.audit_service import record_audit

INVENTORY_STATUSES = {"in_stock", "low_stock", "out_of_stock"}


def build_operations_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["operations"])

    @router.get("/contracts")
    def contracts(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        rows = ContractRepository(db).list_by_org(claims_org_id(claims))
        return [contract_to_dict(c) for c in rows]

    @router.get("/inventory/items")
    def inventory(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        rows = InventoryItemRepository(db).list_by_org(claims_org_id(claims))
        return [inventory_to_dict(i) for i in rows]

    @router.post("/inventory/items", status_code=status.HTTP_201_CREATED)
    def create_inventory_item(
        body: InventoryItemCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("inventory.write")),
    ) -> dict:
        qty = body.quantity
        reorder = body.reorderLevel
        derived = InventoryItemRepository.derive_status(qty, reorder)
        status_val = body.status if body.status in INVENTORY_STATUSES else derived
        item = InventoryItemRepository(db).create(
            claims_org_id(claims),
            sku=body.sku.strip().upper(),
            name=body.name.strip(),
            category=body.category.strip(),
            quantity=qty,
            reorder_level=reorder,
            warehouse=body.warehouse.strip(),
            unit_price=body.unitPrice,
            status=status_val,
        )
        record_audit(db, claims, action="CREATE", resource="InventoryItem", resource_id=item.id, details=item.sku, request=request)
        if item.status == "low_stock":
            from app.services.event_bus import EventBus

            EventBus(db).publish(
                org_id=claims_org_id(claims),
                event_type="inventory.stock.low",
                payload={"itemId": item.id, "sku": item.sku, "quantity": item.quantity},
                source="inventory",
            )
        db.commit()
        db.refresh(item)
        return inventory_to_dict(item)

    @router.patch("/inventory/items/{item_id}")
    def update_inventory_item(
        item_id: str,
        body: InventoryItemUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("inventory.write")),
    ) -> dict:
        if body.status is not None and body.status not in INVENTORY_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = InventoryItemRepository(db)
        item = repo.get_by_id(claims_org_id(claims), item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article introuvable")
        qty = body.quantity if body.quantity is not None else item.quantity
        reorder = body.reorderLevel if body.reorderLevel is not None else item.reorder_level
        status_val = body.status if body.status is not None else InventoryItemRepository.derive_status(qty, reorder)
        repo.update(
            item,
            sku=body.sku.strip().upper() if body.sku else None,
            name=body.name.strip() if body.name else None,
            category=body.category.strip() if body.category else None,
            quantity=body.quantity,
            reorder_level=body.reorderLevel,
            warehouse=body.warehouse.strip() if body.warehouse else None,
            unit_price=body.unitPrice,
            status=status_val,
        )
        record_audit(db, claims, action="UPDATE", resource="InventoryItem", resource_id=item.id, details=item.sku, request=request)
        if item.status == "low_stock":
            from app.services.event_bus import EventBus

            EventBus(db).publish(
                org_id=claims_org_id(claims),
                event_type="inventory.stock.low",
                payload={"itemId": item.id, "sku": item.sku, "quantity": item.quantity},
                source="inventory",
            )
        db.commit()
        db.refresh(item)
        return inventory_to_dict(item)

    return router
