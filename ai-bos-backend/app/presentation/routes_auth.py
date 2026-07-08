from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from app.services.auth_service import AuthService
from app.presentation.deps import require_auth


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4, max_length=128)


class RefreshRequest(BaseModel):
    refreshToken: str = Field(min_length=20)


class AuthResponse(BaseModel):
    user: dict
    token: str
    refreshToken: str


def build_auth_router(auth_service: AuthService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

    @router.post("/login", response_model=AuthResponse)
    def login(payload: LoginRequest):
        token, refresh_token = auth_service.login(payload.email, payload.password)
        user = auth_service.me_from_access_token(token)
        return AuthResponse(user=user, token=token, refreshToken=refresh_token)

    @router.post("/refresh", response_model=AuthResponse)
    def refresh(payload: RefreshRequest):
        token, refresh_token = auth_service.refresh(payload.refreshToken)
        user = auth_service.me_from_access_token(token)
        return AuthResponse(user=user, token=token, refreshToken=refresh_token)

    @router.get("/me")
    def me(claims: dict = Depends(require_auth)):
        return auth_service.me_from_claims(claims)

    return router
