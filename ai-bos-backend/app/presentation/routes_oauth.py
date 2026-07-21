from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.presentation.routes_auth import AuthResponse
from app.services.auth_service import AuthService
from app.services.oauth_service import (
    SUPPORTED_PROVIDERS,
    build_authorize_url,
    create_oauth_login_code,
    exchange_code_for_profile,
    list_providers,
    mock_profile,
    pop_oauth_login_code,
    pop_oauth_state,
    provider_config,
)


class OAuthMockLoginBody(BaseModel):
    state: str = Field(min_length=8, max_length=128)
    email: EmailStr


class OAuthExchangeBody(BaseModel):
    code: str = Field(min_length=20, max_length=256)


def build_oauth_router(auth_service: AuthService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth/oauth", tags=["oauth"])

    @router.get("/providers")
    def oauth_providers() -> dict:
        return {"items": list_providers()}

    @router.get("/{provider}/authorize")
    def oauth_authorize(
        provider: str,
        redirect: bool = Query(default=False),
    ):
        provider = provider.lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider inconnu")
        redirect_uri = f"{settings.api_public_url}/api/v1/auth/oauth/{provider}/callback"
        try:
            payload = build_authorize_url(provider, redirect_uri)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
        if redirect and payload["mode"] == "live":
            return RedirectResponse(payload["authorizationUrl"])
        return payload

    @router.get("/{provider}/callback")
    def oauth_callback(
        provider: str,
        code: str | None = None,
        state: str | None = None,
        error: str | None = None,
    ):
        provider = provider.lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider inconnu")
        if error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth error: {error}")
        if not state:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="state manquant")
        stored = pop_oauth_state(state)
        if not stored or stored.get("provider") != provider:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="state invalide ou expiré")

        cfg = provider_config(provider)
        if cfg["mode"] == "mock":
            # Callback in mock mode is unused; redirect to frontend login.
            return RedirectResponse(f"{settings.app_public_url}/login?oauth={provider}&error=use_mock_login")

        if not code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="code manquant")
        try:
            profile = exchange_code_for_profile(
                provider,
                code,
                stored["redirect_uri"],
                stored["code_verifier"],
            )
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Échange OAuth échoué: {exc}") from exc

        token, refresh = auth_service.login_oauth_profile(
            provider=provider,
            subject=profile["subject"],
            email=profile["email"],
            first_name=profile["first_name"],
            last_name=profile["last_name"],
        )
        login_code = create_oauth_login_code(token=token, refresh_token=refresh)
        query = urlencode({"oauth_code": login_code, "oauth": provider})
        return RedirectResponse(f"{settings.app_public_url}/login?{query}")

    @router.post("/exchange", response_model=AuthResponse)
    def oauth_exchange(body: OAuthExchangeBody):
        payload = pop_oauth_login_code(body.code)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Code OAuth invalide ou expiré",
            )
        token = payload["token"]
        refresh = payload["refresh_token"]
        user = auth_service.me_from_access_token(token)
        return AuthResponse(user=user, token=token, refreshToken=refresh)

    @router.post("/{provider}/mock-login", response_model=AuthResponse)
    def oauth_mock_login(provider: str, body: OAuthMockLoginBody):
        provider = provider.lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider inconnu")
        cfg = provider_config(provider)
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mock OAuth indisponible",
            )
        if cfg["mode"] != "mock":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mock OAuth désactivé (credentials live présents)")
        stored = pop_oauth_state(body.state)
        if not stored or stored.get("provider") != provider:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="state invalide ou expiré")

        profile = mock_profile(provider, str(body.email))
        token, refresh = auth_service.login_oauth_profile(
            provider=provider,
            subject=profile["subject"],
            email=profile["email"],
            first_name=profile["first_name"],
            last_name=profile["last_name"],
        )
        user = auth_service.me_from_access_token(token)
        return AuthResponse(user=user, token=token, refreshToken=refresh)

    return router
