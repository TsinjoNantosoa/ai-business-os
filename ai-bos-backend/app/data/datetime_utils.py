from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def days_ago(n: int) -> str:
    return (_now() - timedelta(days=n)).isoformat()


def days_from_now(n: int) -> str:
    return (_now() + timedelta(days=n)).isoformat()


def hours_ago(n: int) -> str:
    return (_now() - timedelta(hours=n)).isoformat()


def hours_from_now(n: int) -> str:
    return (_now() + timedelta(hours=n)).isoformat()
