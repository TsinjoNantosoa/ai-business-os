from __future__ import annotations

import os
from pathlib import Path

import pytest

TEST_DB_PATH = Path(__file__).resolve().parent.parent / ".pytest_aibos.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> None:
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    from app.core.migrations import run_migrations
    from app.core.database import SessionLocal
    from app.services.bootstrap import bootstrap_demo_data

    run_migrations()
    with SessionLocal() as session:
        bootstrap_demo_data(session)

    yield

    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            pass
