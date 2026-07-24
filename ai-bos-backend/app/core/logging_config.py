from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Keep any "extra" fields that were explicitly provided in log_event
        for k, v in getattr(record, "extra_fields", {}).items():
            payload[k] = v
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
    record = {"event": event, **extra}
    logger.log(level, event, extra={"extra_fields": record})

