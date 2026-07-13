from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contact import Contact


class ContactRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[Contact]:
        stmt = select(Contact).where(Contact.org_id == org_id).order_by(Contact.created_at.desc())
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, contact_id: str) -> Contact | None:
        stmt = select(Contact).where(Contact.org_id == org_id, Contact.id == contact_id)
        return self._session.scalars(stmt).first()

    def count_by_org(self, org_id: str) -> int:
        return len(self.list_by_org(org_id))

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Contact)).all()))

    def create(
        self,
        *,
        org_id: str,
        first_name: str,
        last_name: str,
        email: str,
        company: str,
        owner_id: str,
        owner_name: str | None = None,
        phone: str | None = None,
        position: str | None = None,
        status: str = "active",
        tags: list[str] | None = None,
        avatar_color: str | None = "bg-primary-100",
    ) -> Contact:
        now = datetime.now(timezone.utc)
        contact = Contact(
            id=f"contact-{secrets.token_hex(6)}",
            org_id=org_id,
            first_name=first_name,
            last_name=last_name,
            email=email.lower().strip(),
            phone=phone,
            company=company,
            position=position,
            status=status,
            owner_id=owner_id,
            owner_name=owner_name,
            tags=tags or [],
            avatar_color=avatar_color,
            last_activity_at=now,
            created_at=now,
            updated_at=now,
        )
        self._session.add(contact)
        self._session.flush()
        return contact

    def update(self, contact: Contact, **fields: object) -> Contact:
        for key, value in fields.items():
            if value is not None and hasattr(contact, key):
                setattr(contact, key, value)
        contact.updated_at = datetime.now(timezone.utc)
        contact.last_activity_at = datetime.now(timezone.utc)
        return contact

    def delete(self, contact: Contact) -> None:
        self._session.delete(contact)
