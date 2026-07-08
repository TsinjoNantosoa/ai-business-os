from __future__ import annotations

from threading import Lock
from typing import Any


_COUNTERS: dict[str, int] = {}
_LOCK = Lock()


def inc(name: str, amount: int = 1, **_labels: Any) -> None:
    with _LOCK:
        _COUNTERS[name] = _COUNTERS.get(name, 0) + amount


def snapshot() -> dict[str, int]:
    with _LOCK:
        return dict(_COUNTERS)

