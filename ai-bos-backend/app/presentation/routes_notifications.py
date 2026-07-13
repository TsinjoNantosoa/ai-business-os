from __future__ import annotations

import queue
from collections.abc import Iterator

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.presentation.deps import claims_org_id, claims_user_id, require_auth
from app.presentation.serializers import notification_to_dict
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_hub import encode_sse, notification_hub


def _claims_from_token(token: str) -> dict:
    try:
        return decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token invalide") from exc


def build_notifications_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/platform", tags=["notifications"])

    @router.get("/notifications")
    def list_notifications(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> list[dict]:
        org_id = claims_org_id(claims)
        user_id = claims_user_id(claims)
        rows = NotificationRepository(db).list_for_user(org_id, user_id=user_id)
        return [notification_to_dict(row) for row in rows]

    @router.post("/notifications/{notification_id}/read")
    def mark_notification_read(
        notification_id: str,
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        org_id = claims_org_id(claims)
        repo = NotificationRepository(db)
        notification = repo.get_by_id(org_id, notification_id)
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification introuvable")
        user_id = claims_user_id(claims)
        if notification.user_id and notification.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification introuvable")
        return notification_to_dict(repo.mark_read(notification))

    @router.post("/notifications/read-all")
    def mark_all_notifications_read(
        db: Session = Depends(get_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        count = NotificationRepository(db).mark_all_read(claims_org_id(claims), claims_user_id(claims))
        return {"updated": count}

    @router.get("/notifications/stream")
    def stream_notifications(
        access_token: str | None = Query(default=None),
        max_events: int | None = Query(default=None, ge=1, le=100),
        authorization: str | None = Header(default=None),
        db: Session = Depends(get_db),
    ) -> StreamingResponse:
        token = (access_token or "").strip()
        if not token and authorization and authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requis")

        claims = _claims_from_token(token)
        org_id = claims_org_id(claims)
        if not org_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant manquant")

        _ = NotificationRepository(db).list_for_user(org_id, user_id=claims_user_id(claims), limit=1)

        def event_generator() -> Iterator[str]:
            q = notification_hub.subscribe(org_id)
            sent = 0
            try:
                yield encode_sse({"type": "connected", "orgId": org_id})
                sent += 1
                if max_events is not None and sent >= max_events:
                    return
                while True:
                    try:
                        event = q.get(timeout=5 if max_events else 20)
                        yield encode_sse(event)
                        sent += 1
                        if max_events is not None and sent >= max_events:
                            return
                    except queue.Empty:
                        if max_events is not None:
                            return
                        yield ": ping\n\n"
            finally:
                notification_hub.unsubscribe(org_id, q)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router
