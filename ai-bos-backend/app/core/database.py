from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


def _engine_kwargs() -> dict:
    kwargs: dict = {
        "echo": settings.database_echo,
        "pool_pre_ping": not settings.is_sqlite,
    }
    if settings.is_sqlite:
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # Neon / Render / managed Postgres: keep pool modest for serverless-ish limits.
        kwargs["pool_size"] = settings.database_pool_size
        kwargs["max_overflow"] = settings.database_max_overflow
        kwargs["pool_recycle"] = 1800
    return kwargs


engine = create_engine(settings.database_url, **_engine_kwargs())

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_connection, connection_record) -> None:
    if settings.is_sqlite:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    if not settings.is_sqlite:
        # FastAPI may construct this generator before resolving the auth
        # dependency. The transaction starts only on the first query, by which
        # time require_auth has populated the request ContextVar.
        def _apply_request_tenant(_session, _transaction, connection) -> None:
            from app.core.tenant import get_current_org_id

            org_id = get_current_org_id()
            if org_id:
                connection.execute(
                    text("SELECT set_config('app.current_org_id', :org, true)"),
                    {"org": org_id},
                )

        event.listen(db, "after_begin", _apply_request_tenant)
    try:
        yield db
    finally:
        db.close()


def backend_root() -> Path:
    return Path(__file__).resolve().parents[2]
