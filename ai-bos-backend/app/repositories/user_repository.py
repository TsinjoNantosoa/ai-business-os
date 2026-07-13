from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower().strip())
        return self._session.scalars(stmt).first()

    def get_by_id(self, user_id: str) -> User | None:
        return self._session.get(User, user_id)

    def list_all(self) -> list[User]:
        return list(self._session.scalars(select(User).order_by(User.id)).all())

    def list_by_org(self, org_id: str) -> list[User]:
        stmt = select(User).where(User.org_id == org_id).order_by(User.last_name, User.first_name)
        return list(self._session.scalars(stmt).all())

    def count(self) -> int:
        return len(self.list_all())

    def create(
        self,
        *,
        org_id: str,
        email: str,
        first_name: str,
        last_name: str,
        role: str,
        permissions: list[str],
        password_hash: str,
        active: bool = True,
    ) -> User:
        user = User(
            id=f"u-{secrets.token_hex(8)}",
            org_id=org_id,
            email=email.lower().strip(),
            first_name=first_name,
            last_name=last_name,
            role=role,
            permissions=permissions,
            password_hash=password_hash,
            active=active,
        )
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user
