from __future__ import annotations

from app.core.config import Settings


def test_cors_includes_app_public_url(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    monkeypatch.setenv("APP_PUBLIC_URL", "https://ai-business-os-murex.vercel.app/")
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    settings = Settings.from_env()
    assert "https://ai-business-os-murex.vercel.app" in settings.cors_origins
    assert all(not o.endswith("/") for o in settings.cors_origins)
