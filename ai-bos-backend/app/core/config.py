from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        backend_dir = Path(__file__).resolve().parents[2]
        load_dotenv(backend_dir / ".env", override=True)
    except ImportError:
        pass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


_load_dotenv()


class Settings(BaseModel):
    app_name: str = "AI BOS Backend"
    environment: str = "development"
    jwt_secret: str = Field(default="change-me-in-production-please-use-32-plus-bytes", min_length=16)
    jwt_algorithm: str = "HS256"
    access_token_exp_minutes: int = 60
    refresh_token_exp_days: int = 7
    max_refresh_sessions_per_user: int = 5
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    @classmethod
    def from_env(cls) -> "Settings":
        cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
        return cls(
            app_name=os.getenv("APP_NAME", "AI BOS Backend"),
            environment=os.getenv("ENVIRONMENT", "development"),
            jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production-please-use-32-plus-bytes"),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_exp_minutes=int(os.getenv("ACCESS_TOKEN_EXP_MINUTES", "60")),
            refresh_token_exp_days=int(os.getenv("REFRESH_TOKEN_EXP_DAYS", "7")),
            max_refresh_sessions_per_user=int(os.getenv("MAX_REFRESH_SESSIONS", "5")),
            cors_origins=origins or ["http://localhost:5173"],
        )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings.from_env()

if settings.is_production and settings.jwt_secret.startswith("change-me"):
    raise RuntimeError("JWT_SECRET doit être défini en production.")
