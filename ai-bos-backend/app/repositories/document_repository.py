from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[Document]:
        stmt = select(Document).where(Document.org_id == org_id)
        docs = list(self._session.scalars(stmt).all())
        return sorted(docs, key=lambda d: (0 if d.type == "folder" else 1, d.name.lower()))

    def get_by_id(self, org_id: str, document_id: str) -> Document | None:
        stmt = select(Document).where(Document.org_id == org_id, Document.id == document_id)
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Document)).all()))

    def create(
        self,
        *,
        org_id: str,
        name: str,
        doc_type: str,
        size: int,
        modified_by: str,
        parent_id: str | None = None,
        storage_key: str | None = None,
        mime_type: str | None = None,
        starred: bool = False,
    ) -> Document:
        now = datetime.now(timezone.utc)
        document = Document(
            id=f"doc-{secrets.token_hex(6)}",
            org_id=org_id,
            name=name,
            type=doc_type,
            size=size,
            parent_id=parent_id,
            storage_key=storage_key,
            mime_type=mime_type,
            starred=starred,
            modified_by=modified_by,
            modified_at=now,
            created_at=now,
        )
        self._session.add(document)
        self._session.flush()
        return document
