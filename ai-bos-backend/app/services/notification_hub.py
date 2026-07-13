from __future__ import annotations

import json
import queue
import threading
from collections import defaultdict
from typing import Any


class NotificationHub:
    """In-process pub/sub for in-app notification SSE (per org)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[queue.Queue]] = defaultdict(list)

    def subscribe(self, org_id: str) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=100)
        with self._lock:
            self._subscribers[org_id].append(q)
        return q

    def unsubscribe(self, org_id: str, q: queue.Queue) -> None:
        with self._lock:
            subs = self._subscribers.get(org_id, [])
            if q in subs:
                subs.remove(q)
            if not subs and org_id in self._subscribers:
                del self._subscribers[org_id]

    def publish(self, org_id: str, event: dict[str, Any]) -> None:
        with self._lock:
            subscribers = list(self._subscribers.get(org_id, []))
        for q in subscribers:
            try:
                q.put_nowait(event)
            except queue.Full:
                pass


notification_hub = NotificationHub()


def encode_sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
