from __future__ import annotations

from app.core.config import normalize_database_url


def test_normalize_postgres_scheme_and_ssl() -> None:
    url = normalize_database_url("postgres://u:p@host/db", require_ssl=True)
    assert url.startswith("postgresql+psycopg2://")
    assert "sslmode=require" in url


def test_normalize_keeps_existing_sslmode() -> None:
    url = normalize_database_url(
        "postgresql://u:p@host/db?sslmode=verify-full",
        require_ssl=True,
    )
    assert "sslmode=verify-full" in url
    assert url.count("sslmode=") == 1


def test_normalize_sqlite_unchanged() -> None:
    assert normalize_database_url("sqlite:///./aibos.db", require_ssl=True) == "sqlite:///./aibos.db"
