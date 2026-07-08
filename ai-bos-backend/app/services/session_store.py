from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock


@dataclass
class RefreshSession:
    session_id: str
    user_id: str
    created_at: datetime
    revoked: bool = False


class InMemoryRefreshSessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, RefreshSession] = {}
        self._lock = Lock()

    def save(self, session: RefreshSession) -> None:
        with self._lock:
            self._sessions[session.session_id] = session

    def get(self, session_id: str) -> RefreshSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def revoke(self, session_id: str) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.revoked = True

    def revoke_all_for_user(self, user_id: str) -> None:
        with self._lock:
            for session in self._sessions.values():
                if session.user_id == user_id:
                    session.revoked = True

    def count_active_for_user(self, user_id: str) -> int:
        with self._lock:
            return sum(
                1
                for s in self._sessions.values()
                if s.user_id == user_id and not s.revoked and s.created_at <= datetime.now(tz=timezone.utc)
            )
