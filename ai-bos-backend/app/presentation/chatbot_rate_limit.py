from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from time import time


@dataclass
class _Window:
    hits: deque[float] = field(default_factory=deque)


class ChatbotRateLimiter:
    def __init__(self, max_per_minute: int = 20) -> None:
        self.max_per_minute = max_per_minute
        self._lock = Lock()
        self._windows: dict[str, _Window] = {}

    def check(self, key: str, max_per_minute: int | None = None) -> int | None:
        limit = self.max_per_minute if max_per_minute is None else max(1, int(max_per_minute))
        now = time()
        with self._lock:
            window = self._windows.setdefault(key, _Window())
            while window.hits and now - window.hits[0] > 60:
                window.hits.popleft()
            if len(window.hits) >= limit:
                retry = int(60 - (now - window.hits[0]))
                return max(retry, 1)
            window.hits.append(now)
            return None

    def reset(self) -> None:
        with self._lock:
            self._windows.clear()

    def reset_key(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)
