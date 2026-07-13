from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.models.kb import KbChunk, KbDocument


class KbRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def count_chunks(self, org_id: str | None = None) -> int:
        stmt = select(KbChunk)
        if org_id:
            stmt = stmt.where(or_(KbChunk.org_id == org_id, KbChunk.org_id == "platform"))
        return len(self.db.scalars(stmt).all())

    def get_document_by_hash(self, org_id: str, content_hash: str) -> KbDocument | None:
        return self.db.scalar(
            select(KbDocument).where(KbDocument.org_id == org_id, KbDocument.content_hash == content_hash)
        )

    def delete_document_cascade(self, document_id: str) -> None:
        self.db.execute(delete(KbChunk).where(KbChunk.document_id == document_id))
        self.db.execute(delete(KbDocument).where(KbDocument.id == document_id))

    def add_document(self, doc: KbDocument) -> KbDocument:
        self.db.add(doc)
        self.db.flush()
        return doc

    def add_chunk(self, chunk: KbChunk) -> KbChunk:
        self.db.add(chunk)
        return chunk

    def list_chunks_for_search(self, org_id: str) -> list[KbChunk]:
        return list(
            self.db.scalars(
                select(KbChunk).where(or_(KbChunk.org_id == org_id, KbChunk.org_id == "platform"))
            ).all()
        )

    def get_documents_map(self, document_ids: list[str]) -> dict[str, KbDocument]:
        if not document_ids:
            return {}
        rows = self.db.scalars(select(KbDocument).where(KbDocument.id.in_(document_ids))).all()
        return {row.id: row for row in rows}

    def list_documents(self, org_id: str, *, limit: int = 100) -> list[KbDocument]:
        return list(
            self.db.scalars(
                select(KbDocument)
                .where(or_(KbDocument.org_id == org_id, KbDocument.org_id == "platform"))
                .order_by(KbDocument.updated_at.desc())
                .limit(limit)
            ).all()
        )

    def wipe_source_type(self, org_id: str, source_type: str) -> int:
        docs = list(
            self.db.scalars(
                select(KbDocument).where(KbDocument.org_id == org_id, KbDocument.source_type == source_type)
            ).all()
        )
        for doc in docs:
            self.delete_document_cascade(doc.id)
        return len(docs)

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def dumps(data: object | None) -> str | None:
        if data is None:
            return None
        return json.dumps(data, ensure_ascii=False)

    @staticmethod
    def loads(raw: str | None, default=None):
        if not raw:
            return default
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return default
