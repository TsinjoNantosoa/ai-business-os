from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_org(self, org_id: str) -> list[Task]:
        stmt = select(Task).where(Task.org_id == org_id).order_by(Task.due_date.asc())
        return list(self._session.scalars(stmt).all())

    def get_by_id(self, org_id: str, task_id: str) -> Task | None:
        stmt = select(Task).where(Task.org_id == org_id, Task.id == task_id)
        return self._session.scalars(stmt).first()

    def count_all(self) -> int:
        return len(list(self._session.scalars(select(Task)).all()))

    def update_status(self, task: Task, status: str) -> Task:
        task.status = status
        task.updated_at = datetime.now(timezone.utc)
        return task

    def assign(
        self,
        task: Task,
        *,
        assignee_id: str,
        assignee_name: str,
        assignee_avatar_color: str | None = None,
    ) -> Task:
        task.assignee_id = assignee_id
        task.assignee_name = assignee_name
        if assignee_avatar_color:
            task.assignee_avatar_color = assignee_avatar_color
        task.updated_at = datetime.now(timezone.utc)
        return task
