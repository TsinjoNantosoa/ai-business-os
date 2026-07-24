from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from pydantic import BaseModel, Field


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        backend_dir = Path(__file__).resolve().parents[2]
        # override=False: real env vars win over .env, so pytest's DATABASE_URL
        # (test DB) isn't silently replaced by the dev aibos.db.
        load_dotenv(backend_dir / ".env", override=False)
    except ImportError:
        pass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_rate_limit_per_minute(*names: str, default: int = 20) -> int:
    for name in names:
        raw = os.getenv(name)
        if not raw:
            continue
        value = raw.strip()
        if "/" in value:
            value = value.split("/", 1)[0].strip()
        try:
            return max(1, int(value))
        except ValueError:
            continue
    return default


def normalize_database_url(url: str, *, require_ssl: bool) -> str:
    """Normalize Neon/Render URLs and ensure SSL for cloud Postgres."""
    value = (url or "").strip()
    if not value:
        return "sqlite:///./aibos.db"

    # Neon / Heroku sometimes provide postgres:// — SQLAlchemy wants postgresql://
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]
    if value.startswith("postgresql://") and "+psycopg2" not in value and "+asyncpg" not in value:
        value = "postgresql+psycopg2://" + value[len("postgresql://") :]

    if require_ssl and value.startswith("postgresql"):
        parsed = urlparse(value)
        qs = parse_qs(parsed.query)
        if "sslmode" not in qs:
            qs["sslmode"] = ["require"]
            value = urlunparse(parsed._replace(query=urlencode(qs, doseq=True)))
    return value


_load_dotenv()


class Settings(BaseModel):
    app_name: str = "AI BOS Backend"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./aibos.db"
    database_echo: bool = False
    database_pool_size: int = 5
    database_max_overflow: int = 10
    seed_demo_data: bool = True
    jwt_secret: str = Field(default="change-me-in-production-please-use-32-plus-bytes", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60
    refresh_token_exp_days: int = 7
    max_refresh_sessions_per_user: int = 5
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    app_public_url: str = "http://localhost:5173"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    chatbot_api_token: str | None = None
    chatbot_query_rate_limit: int = 20
    storage_local_path: str = "./storage"
    s3_endpoint_url: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_bucket: str = "aibos-documents"
    s3_region: str = "us-east-1"
    google_client_id: str | None = None
    google_client_secret: str | None = None
    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = None
    microsoft_tenant_id: str = "common"
    api_public_url: str = "http://localhost:8000"
    backup_dir: str = "./backups"
    password_reset_exp_minutes: int = 60
    email_mode: str = "log"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_use_tls: bool = True
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "AI BOS <noreply@aibos.local>"

    @classmethod
    def from_env(cls) -> "Settings":
        environment = os.getenv("ENVIRONMENT", "development")
        is_prod = environment.lower() == "production"
        cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        origins = [o.strip().rstrip("/") for o in cors_raw.split(",") if o.strip()]
        # Never allow wildcard with credentials in production.
        if is_prod:
            origins = [o for o in origins if o != "*"]

        # Also allow the public frontend URL when set (Vercel).
        app_public = (os.getenv("APP_PUBLIC_URL") or "").strip().rstrip("/")
        if app_public and app_public not in origins and app_public != "*":
            origins.append(app_public)

        raw_db = os.getenv("DATABASE_URL", "sqlite:///./aibos.db")
        database_url = normalize_database_url(raw_db, require_ssl=is_prod and "sqlite" not in raw_db)

        # SECRET_KEY is accepted as alias for JWT_SECRET (common PaaS naming).
        jwt_secret = (
            os.getenv("JWT_SECRET")
            or os.getenv("SECRET_KEY")
            or "change-me-in-production-please-use-32-plus-bytes"
        )

        smtp_user = os.getenv("SMTP_USER") or os.getenv("SMTP_USERNAME") or None
        smtp_password = os.getenv("SMTP_PASSWORD") or None

        seed_default = not is_prod
        return cls(
            app_name=os.getenv("APP_NAME", "AI BOS Backend"),
            environment=environment,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            database_url=database_url,
            database_echo=_env_bool("DATABASE_ECHO", False),
            database_pool_size=int(os.getenv("DATABASE_POOL_SIZE", "5")),
            database_max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
            seed_demo_data=_env_bool("SEED_DEMO_DATA", seed_default),
            jwt_secret=jwt_secret,
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_exp_minutes=int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "60")),
            refresh_token_exp_days=int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "7")),
            max_refresh_sessions_per_user=int(os.getenv("MAX_REFRESH_SESSIONS", "5")),
            cors_origins=origins or ["http://localhost:5173"],
            stripe_secret_key=os.getenv("STRIPE_SECRET_KEY") or None,
            stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET") or None,
            app_public_url=os.getenv("APP_PUBLIC_URL", "http://localhost:5173"),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY") or None,
            chatbot_api_token=os.getenv("CHATBOT_API_TOKEN") or None,
            chatbot_query_rate_limit=_parse_rate_limit_per_minute(
                "QUERY_RATE_LIMIT",
                "CHATBOT_QUERY_RATE_LIMIT",
                default=20,
            ),
            storage_local_path=os.getenv("STORAGE_LOCAL_PATH", "./storage"),
            s3_endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
            s3_access_key=os.getenv("S3_ACCESS_KEY") or os.getenv("MINIO_ACCESS_KEY") or None,
            s3_secret_key=os.getenv("S3_SECRET_KEY") or os.getenv("MINIO_SECRET_KEY") or None,
            s3_bucket=os.getenv("S3_BUCKET", "aibos-documents"),
            s3_region=os.getenv("S3_REGION", "us-east-1"),
            google_client_id=os.getenv("GOOGLE_CLIENT_ID") or None,
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET") or None,
            microsoft_client_id=os.getenv("MICROSOFT_CLIENT_ID") or None,
            microsoft_client_secret=os.getenv("MICROSOFT_CLIENT_SECRET") or None,
            microsoft_tenant_id=os.getenv("MICROSOFT_TENANT_ID", "common"),
            api_public_url=os.getenv("API_PUBLIC_URL", "http://localhost:8000"),
            backup_dir=os.getenv("BACKUP_DIR", "./backups"),
            password_reset_exp_minutes=int(os.getenv("PASSWORD_RESET_EXP_MINUTES", "60")),
            email_mode=os.getenv("EMAIL_MODE", "log"),
            smtp_host=os.getenv("SMTP_HOST") or None,
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_use_tls=_env_bool("SMTP_USE_TLS", True),
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            smtp_from=os.getenv("SMTP_FROM", "AI BOS <noreply@aibos.local>"),
        )

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings.from_env()

if settings.is_production and settings.jwt_secret.startswith("change-me"):
    raise RuntimeError("JWT_SECRET (or SECRET_KEY) must be set to a strong value in production.")

if settings.is_production and ("*" in settings.cors_origins):
    raise RuntimeError("CORS_ORIGINS must not include '*' in production.")
