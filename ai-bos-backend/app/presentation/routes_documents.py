from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.presentation.deps import claims_org_id, require_permission
from app.presentation.serializers import document_to_dict
from app.repositories.document_repository import DocumentRepository
from app.services.audit_service import record_audit
from app.services.storage_service import StorageService

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".pdf": ("pdf", "application/pdf"),
    ".docx": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ".doc": ("docx", "application/msword"),
    ".xlsx": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ".xls": ("xlsx", "application/vnd.ms-excel"),
    ".png": ("image", "image/png"),
    ".jpg": ("image", "image/jpeg"),
    ".jpeg": ("image", "image/jpeg"),
    ".gif": ("image", "image/gif"),
    ".webp": ("image", "image/webp"),
}


def _detect_type(filename: str, content_type: str | None) -> tuple[str, str]:
    lower = filename.lower()
    for ext, (doc_type, mime) in ALLOWED_EXTENSIONS.items():
        if lower.endswith(ext):
            return doc_type, content_type or mime
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Type de fichier non supporté (PDF, DOCX, XLSX, images)",
    )


def build_documents_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
    storage = StorageService()

    @router.get("")
    def list_documents(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("document.read")),
    ) -> list[dict]:
        documents = DocumentRepository(db).list_by_org(claims_org_id(claims))
        return [document_to_dict(document) for document in documents]

    @router.post("/upload", status_code=status.HTTP_201_CREATED)
    async def upload_document(
        request: Request,
        file: UploadFile = File(...),
        parentId: str | None = Form(default=None),
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("document.write")),
    ) -> dict:
        org_id = claims_org_id(claims)
        filename = file.filename or "upload.bin"
        doc_type, mime_type = _detect_type(filename, file.content_type)
        data = await file.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier trop volumineux (10MB max)")
        if not data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier vide")

        if parentId:
            parent = DocumentRepository(db).get_by_id(org_id, parentId)
            if not parent or parent.type != "folder":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dossier parent invalide")

        key = storage.build_key(org_id, filename)
        storage.save(key, data, mime_type)
        modified_by = f"{claims.get('first_name', '')} {claims.get('last_name', '')}".strip() or "User"
        document = DocumentRepository(db).create(
            org_id=org_id,
            name=filename,
            doc_type=doc_type,
            size=len(data),
            modified_by=modified_by,
            parent_id=parentId,
            storage_key=key,
            mime_type=mime_type,
        )
        record_audit(db, claims, action="CREATE", resource="Document", resource_id=document.id, details=filename, request=request)
        db.commit()
        db.refresh(document)
        return document_to_dict(document)

    @router.get("/{document_id}/download")
    def download_document(
        document_id: str,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_permission("document.read")),
    ) -> Response:
        document = DocumentRepository(db).get_by_id(claims_org_id(claims), document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable")
        if document.type == "folder":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Impossible de télécharger un dossier")
        if not document.storage_key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier non disponible (métadonnées seed uniquement)")

        try:
            payload = storage.read(document.storage_key)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable sur le stockage") from exc

        return Response(
            content=payload,
            media_type=document.mime_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{document.name}"'},
        )

    return router
