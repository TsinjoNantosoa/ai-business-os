from __future__ import annotations

import json
import logging
import re
import sys
from datetime import datetime, timezone

_SENSITIVE_KEY = re.compile(r"password|secret|token|authorization|cookie|api.?key|stripe.?signature", re.I)
_BEARER = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+\-/]+=*")
_API_KEY = re.compile(r"aibos_sk_[A-Za-z0-9_\-]+")


def sanitize_log_value(value):
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _SENSITIVE_KEY.search(str(key)) else sanitize_log_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_log_value(item) for item in value]
    if isinstance(value, str):
        return _API_KEY.sub("[REDACTED_API_KEY]", _BEARER.sub("Bearer [REDACTED]", value))[:4000]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_log_value(record.getMessage()),
        }
        # Keep any "extra" fields that were explicitly provided in log_event
        for k, v in getattr(record, "extra_fields", {}).items():
            payload[k] = sanitize_log_value(v)
        return json.dumps(payload, ensure_ascii=True)


_CONFIGURED = False


def configure_logging(*, force: bool = False) -> None:
    global _CONFIGURED
    if _CONFIGURED and not force:
        return

    from app.core.config import settings

    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)

    if force:
        root.handlers.clear()
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)

    # Alembic's fileConfig disables loggers created before migrations run.
    for name in ("aibos", "aibos.auth", "aibos.email", "aibos.platform", "uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(name).disabled = False
        logging.getLogger(name).setLevel(level)

    _CONFIGURED = True


def log_event(logger: logging.Logger, level: int, event: str, **extra) -> None:
    record = sanitize_log_value({"event": event, **extra})
    logger.log(level, event, extra={"extra_fields": record})

