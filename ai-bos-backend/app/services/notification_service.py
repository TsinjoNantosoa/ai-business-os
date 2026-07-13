from __future__ import annotations

from sqlalchemy.orm import Session

from app.presentation.serializers import notification_to_dict
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_hub import notification_hub


def create_and_publish_notification(
    db: Session,
    *,
    org_id: str,
    type: str,
    title: str,
    message: str,
    link: str | None = None,
    user_id: str | None = None,
) -> dict:
    notification = NotificationRepository(db).create(
        org_id=org_id,
        type=type,
        title=title,
        message=message,
        link=link,
        user_id=user_id,
    )
    payload = notification_to_dict(notification)
    notification_hub.publish(org_id, {"type": "notification", "notification": payload})
    return payload
