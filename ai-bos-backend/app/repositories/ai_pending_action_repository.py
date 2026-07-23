from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_pending_action import AiPendingAction


class AiPendingActionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        org_id: str,
        user_id: str,
        tool_name: str,
        arguments: dict,
        call_id: str,
        user_message: str,
        conversation_id: str | None = None,
        agent_id: str | None = None,
    ) -> AiPendingAction:
        now = datetime.now(timezone.utc)
        row = AiPendingAction(
            id=f"hitl-{secrets.token_hex(8)}",
            org_id=org_id,
            conversation_id=conversation_id,
            user_id=user_id,
            agent_id=agent_id,
            tool_name=tool_name,
            arguments=arguments or {},
            call_id=call_id,
            user_message=user_message or "",
            status="pending",
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_by_id(self, org_id: str, action_id: str) -> AiPendingAction | None:
        stmt = select(AiPendingAction).where(
            AiPendingAction.org_id == org_id,
            AiPendingAction.id == action_id,
        )
        return self._session.scalars(stmt).first()

    def list_by_org(
        self,
        org_id: str,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[AiPendingAction]:
        stmt = select(AiPendingAction).where(AiPendingAction.org_id == org_id)
        if status:
            stmt = stmt.where(AiPendingAction.status == status)
        stmt = stmt.order_by(AiPendingAction.created_at.desc()).limit(max(1, min(limit, 100)))
        return list(self._session.scalars(stmt).all())
