from __future__ import annotations

import logging
import time
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings
from app.core.database import backend_root

logger = logging.getLogger("aibos")


def run_migrations(*, retries: int = 5, delay_seconds: float = 2.0) -> None:
    """Apply Alembic migrations with retries (Neon cold start / network blips)."""
    cfg = Config(str(backend_root() / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            command.upgrade(cfg, "head")
            return
        except Exception as exc:  # noqa: BLE001 — retry then re-raise
            last_error = exc
            logger.warning(
                "migration_attempt_failed attempt=%s/%s error=%s",
                attempt,
                retries,
                type(exc).__name__,
            )
            if attempt < retries:
                time.sleep(delay_seconds * attempt)
    assert last_error is not None
    raise last_error
