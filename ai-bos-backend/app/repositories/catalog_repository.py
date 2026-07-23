"""Repository helpers for catalog entities + org JSON datasets."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import (
    AiAgent,
    Candidate,
    Contract,
    Employee,
    FinanceTransaction,
    InventoryItem,
    JobOpening,
    KnowledgeArticle,
    OrgDataset,
    PurchaseOrder,
    Supplier,
)

T = TypeVar("T")


class CatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_org(self, model: type[T], org_id: str) -> list[T]:
        return self.db.query(model).filter_by(org_id=org_id).all()

    def count_by_org(self, model: type[T], org_id: str) -> int:
        return self.db.query(model).filter_by(org_id=org_id).count()

    def count_all(self, model: type[T]) -> int:
        return self.db.query(model).count()

    def get_dataset(self, org_id: str, key: str) -> dict | None:
        row = self.db.query(OrgDataset).filter_by(org_id=org_id, key=key).first()
        return row.payload if row else None

    def upsert_dataset(self, org_id: str, key: str, payload: dict) -> OrgDataset:
        row = self.db.query(OrgDataset).filter_by(org_id=org_id, key=key).first()
        if row:
            row.payload = payload
            return row
        row = OrgDataset(id=f"ds-{uuid4().hex[:12]}", org_id=org_id, key=key, payload=payload)
        self.db.add(row)
        return row

    def get_agent(self, org_id: str, agent_id: str | None) -> AiAgent | None:
        q = self.db.query(AiAgent).filter_by(org_id=org_id)
        if not agent_id:
            return q.order_by(AiAgent.id).first()
        return (
            q.filter((AiAgent.id == agent_id) | (AiAgent.slug == agent_id)).first()
            or q.order_by(AiAgent.id).first()
        )


def employee_to_dict(e: Employee) -> dict:
    return {
        "id": e.id,
        "firstName": e.first_name,
        "lastName": e.last_name,
        "email": e.email,
        "phone": e.phone,
        "position": e.position,
        "department": e.department,
        "startDate": e.start_date,
        "status": e.status,
        "avatarColor": e.avatar_color,
        "salary": e.salary,
        "location": e.location,
        "managerId": e.manager_id,
    }


def job_to_dict(j: JobOpening) -> dict:
    return {
        "id": j.id,
        "title": j.title,
        "department": j.department,
        "status": j.status,
        "applicants": j.applicants,
        "postedDate": j.posted_date,
        "location": j.location,
        "type": j.type,
    }


def candidate_to_dict(c: Candidate) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "jobId": c.job_id,
        "jobTitle": c.job_title,
        "stage": c.stage,
        "score": c.score,
        "avatarColor": c.avatar_color,
        "appliedAt": c.applied_at,
    }


def supplier_to_dict(s: Supplier) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "email": s.email,
        "phone": s.phone,
        "rating": s.rating,
        "country": s.country,
        "status": s.status,
    }


def purchase_order_to_dict(po: PurchaseOrder) -> dict:
    return {
        "id": po.id,
        "poNumber": po.po_number,
        "supplierId": po.supplier_id,
        "supplierName": po.supplier_name,
        "status": po.status,
        "totalAmount": po.total_amount,
        "currency": po.currency,
        "createdAt": po.created_at_iso,
        "expectedAt": po.expected_at,
        "ownerName": po.owner_name,
        "itemCount": po.item_count,
    }


def contract_to_dict(c: Contract) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "type": c.type,
        "counterparty": c.counterparty,
        "value": c.value,
        "currency": c.currency,
        "startDate": c.start_date,
        "endDate": c.end_date,
        "status": c.status,
        "owner": c.owner,
    }


def inventory_to_dict(i: InventoryItem) -> dict:
    return {
        "id": i.id,
        "sku": i.sku,
        "name": i.name,
        "category": i.category,
        "quantity": i.quantity,
        "reorderLevel": i.reorder_level,
        "warehouse": i.warehouse,
        "unitPrice": i.unit_price,
        "status": i.status,
    }


def transaction_to_dict(t: FinanceTransaction) -> dict:
    return {
        "id": t.id,
        "description": t.description,
        "amount": t.amount,
        "type": t.type,
        "category": t.category,
        "date": t.date,
        "account": t.account,
    }


def article_to_dict(a: KnowledgeArticle) -> dict:
    return {
        "id": a.id,
        "title": a.title,
        "category": a.category,
        "excerpt": a.excerpt,
        "content": a.content,
        "author": a.author,
        "updatedAt": a.updated_at_iso,
        "views": a.views,
        "helpful": a.helpful,
    }


def agent_to_dict(a: AiAgent) -> dict:
    return {
        "id": a.id,
        "slug": a.slug,
        "name": a.name,
        "description": a.description,
        "status": a.status,
        "category": a.category,
        "icon": a.icon,
        "toolsCount": a.tools_count,
        "lastUsed": a.last_used,
        "conversations": a.conversations,
    }


# --- Write helpers (Lot catalog CRUD) ---


class _CatalogEntityRepository(Generic[T]):
    model: type[T]
    id_prefix: str

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[T]:
        stmt = select(self.model).where(self.model.org_id == org_id).order_by(self.model.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, entity_id: str) -> T | None:
        stmt = select(self.model).where(self.model.org_id == org_id, self.model.id == entity_id)
        return self._session.scalars(stmt).first()

    def create(self, org_id: str, **fields: Any) -> T:
        now = datetime.now(timezone.utc)
        entity = self.model(
            id=fields.pop("id", None) or f"{self.id_prefix}-{secrets.token_hex(6)}",
            org_id=org_id,
            created_at=now,
            updated_at=now,
            **fields,
        )
        self._session.add(entity)
        self._session.flush()
        return entity

    def update(self, entity: T, **fields: Any) -> T:
        for key, value in fields.items():
            if value is not None:
                setattr(entity, key, value)
        entity.updated_at = datetime.now(timezone.utc)
        self._session.flush()
        return entity


class EmployeeRepository(_CatalogEntityRepository[Employee]):
    model = Employee
    id_prefix = "emp"


class JobOpeningRepository(_CatalogEntityRepository[JobOpening]):
    model = JobOpening
    id_prefix = "job"


class CandidateRepository(_CatalogEntityRepository[Candidate]):
    model = Candidate
    id_prefix = "cand"


class SupplierRepository(_CatalogEntityRepository[Supplier]):
    model = Supplier
    id_prefix = "sup"


class PurchaseOrderRepository(_CatalogEntityRepository[PurchaseOrder]):
    model = PurchaseOrder
    id_prefix = "po"

    def next_po_number(self, org_id: str) -> str:
        count = int(
            self._session.scalar(
                select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.org_id == org_id)
            )
            or 0
        )
        return f"PO-{3000 + count}"


class InventoryItemRepository(_CatalogEntityRepository[InventoryItem]):
    model = InventoryItem
    id_prefix = "inv"

    @staticmethod
    def derive_status(quantity: int, reorder_level: int) -> str:
        if quantity <= 0:
            return "out_of_stock"
        if quantity <= reorder_level:
            return "low_stock"
        return "in_stock"


class FinanceTransactionRepository(_CatalogEntityRepository[FinanceTransaction]):
    model = FinanceTransaction
    id_prefix = "tx"


class ContractRepository(_CatalogEntityRepository[Contract]):
    model = Contract
    id_prefix = "ctr"
