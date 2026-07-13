from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_user(self, org_id: str, user_id: str | None = None, limit: int = 100) -> list[Notification]:
        stmt = select(Notification).where(Notification.org_id == org_id)
        if user_id:
            stmt = stmt.where(or_(Notification.user_id.is_(None), Notification.user_id == user_id))
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, notification_id: str) -> Notification | None:
        stmt = select(Notification).where(
            Notification.org_id == org_id,
            Notification.id == notification_id,
        )
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Notification)).all()))

    def create(
        self,
        *,
        org_id: str,
        type: str,
        title: str,
        message: str,
        link: str | None = None,
        user_id: str | None = None,
        read: bool = False,
    ) -> Notification:
        row = Notification(
            id=f"notif-{secrets.token_hex(8)}",
            org_id=org_id,
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            link=link,
            read=read,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return row

    def mark_read(self, notification: Notification) -> Notification:
        notification.read = True
        self._session.commit()
        self._session.refresh(notification)
        return notification

    def mark_all_read(self, org_id: str, user_id: str | None = None) -> int:
        rows = self.list_for_user(org_id, user_id=user_id, limit=500)
        count = 0
        for row in rows:
            if not row.read:
                row.read = True
                count += 1
        self._session.commit()
        return count
