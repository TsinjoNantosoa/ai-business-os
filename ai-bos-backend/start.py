#!/usr/bin/env python
"""Production entrypoint for Render / Docker / PaaS.

Honours PORT (Render sets this). Runs uvicorn with production-safe defaults.
"""
from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WEB_CONCURRENCY", os.getenv("UVICORN_WORKERS", "1")))
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    # In-memory refresh sessions are not shared across workers — keep 1 unless Redis-backed.
    if workers > 1:
        # Prefer single worker until session store is externalized.
        workers = 1

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        workers=workers,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level=log_level,
        timeout_keep_alive=30,
        timeout_graceful_shutdown=10,
    )


if __name__ == "__main__":
    main()
