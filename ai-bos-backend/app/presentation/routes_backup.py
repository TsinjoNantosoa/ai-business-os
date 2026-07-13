from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.presentation.deps import require_permission
from app.services import backup_service
from app.services.audit_service import record_audit


class CreateBackupBody(BaseModel):
    includeStorage: bool = True


class RestoreBackupBody(BaseModel):
    confirm: str = Field(description='Must be exactly "RESTORE"')
    restoreStorage: bool = True


def build_backup_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/platform/backups", tags=["backups"])

    @router.get("")
    def list_backups(claims: dict = Depends(require_permission("admin.audit"))) -> list[dict]:
        return [
            {
                "id": b.id,
                "path": b.path,
                "createdAt": b.created_at,
                "sizeBytes": b.size_bytes,
                "engine": b.engine,
                "includesStorage": b.includes_storage,
            }
            for b in backup_service.list_backups()
        ]

    @router.post("", status_code=status.HTTP_201_CREATED)
    def create_backup(
        request: Request,
        db: Session = Depends(get_db),
        body: CreateBackupBody | None = None,
        claims: dict = Depends(require_permission("admin.audit")),
    ) -> dict:
        include_storage = True if body is None else body.includeStorage
        try:
            info = backup_service.create_backup(include_storage=include_storage)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        record_audit(
            db,
            claims,
            action="CREATE",
            resource="Backup",
            resource_id=info.id,
            details=f"backup_created size={info.size_bytes}",
            request=request,
        )
        return {
            "id": info.id,
            "path": info.path,
            "createdAt": info.created_at,
            "sizeBytes": info.size_bytes,
            "engine": info.engine,
            "includesStorage": info.includes_storage,
        }

    @router.post("/{backup_id}/restore")
    def restore_backup(
        backup_id: str,
        body: RestoreBackupBody,
        request: Request,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("admin.audit")),
    ) -> dict:
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Restore via API interdit en production — utiliser le CLI / runbook",
            )
        if body.confirm != "RESTORE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='confirm doit être "RESTORE"')
        try:
            result = backup_service.restore_backup(backup_id, restore_storage=body.restoreStorage)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
        record_audit(
            db,
            claims,
            action="UPDATE",
            resource="Backup",
            resource_id=backup_id,
            details="backup_restored",
            request=request,
        )
        return result

    return router
