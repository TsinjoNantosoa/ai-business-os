from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_auth, require_permission
from app.presentation.schemas import EmployeeCreateBody, EmployeeUpdateBody
from app.repositories.catalog_repository import (
    CatalogRepository,
    EmployeeRepository,
    employee_to_dict,
)
from app.services.audit_service import record_audit
from app.services.org_demo_data import get_dataset_for_org

EMPLOYEE_STATUSES = {"active", "on_leave", "terminated", "inactive"}
AVATAR_COLORS = ("bg-primary-100", "bg-emerald-100", "bg-amber-100", "bg-pink-100", "bg-sky-100")


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def build_dashboard_data_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["dashboard-data"])

    @router.get("/finance/overview")
    def finance_overview(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        payload = get_dataset_for_org(db, claims_org_id(claims), "finance_overview")
        if not payload:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vue finance introuvable")
        return payload

    @router.get("/hr/employees")
    def employees(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        rows = EmployeeRepository(db).list_by_org(claims_org_id(claims))
        return [employee_to_dict(e) for e in rows]

    @router.post("/hr/employees", status_code=status.HTTP_201_CREATED)
    def create_employee(
        body: EmployeeCreateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("hr.employee.write")),
    ) -> dict:
        if body.status not in EMPLOYEE_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        org_id = claims_org_id(claims)
        repo = EmployeeRepository(db)
        emp = repo.create(
            org_id,
            first_name=body.firstName.strip(),
            last_name=body.lastName.strip(),
            email=body.email.strip().lower(),
            phone=body.phone,
            position=body.position.strip(),
            department=body.department.strip(),
            start_date=body.startDate or _today(),
            status=body.status,
            avatar_color=body.avatarColor or AVATAR_COLORS[0],
            salary=body.salary,
            location=body.location,
            manager_id=body.managerId,
        )
        record_audit(
            db,
            claims,
            action="CREATE",
            resource="Employee",
            resource_id=emp.id,
            details=emp.email,
            request=request,
        )
        from app.services.event_bus import EventBus

        EventBus(db).publish(
            org_id=org_id,
            event_type="hr.employee.created",
            payload={"employeeId": emp.id, "email": emp.email, "department": emp.department},
            source="hr",
        )
        db.commit()
        db.refresh(emp)
        return employee_to_dict(emp)

    @router.patch("/hr/employees/{employee_id}")
    def update_employee(
        employee_id: str,
        body: EmployeeUpdateBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("hr.employee.write")),
    ) -> dict:
        if body.status is not None and body.status not in EMPLOYEE_STATUSES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut invalide")
        repo = EmployeeRepository(db)
        emp = repo.get_by_id(claims_org_id(claims), employee_id)
        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé introuvable")
        repo.update(
            emp,
            first_name=body.firstName.strip() if body.firstName else None,
            last_name=body.lastName.strip() if body.lastName else None,
            email=body.email.strip().lower() if body.email else None,
            phone=body.phone,
            position=body.position.strip() if body.position else None,
            department=body.department.strip() if body.department else None,
            start_date=body.startDate,
            status=body.status,
            salary=body.salary,
            location=body.location,
            manager_id=body.managerId,
            avatar_color=body.avatarColor,
        )
        record_audit(
            db,
            claims,
            action="UPDATE",
            resource="Employee",
            resource_id=emp.id,
            details=emp.email,
            request=request,
        )
        db.commit()
        db.refresh(emp)
        return employee_to_dict(emp)

    return router
