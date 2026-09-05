from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.presentation.deps import claims_user_id, get_tenant_db, require_auth
from app.presentation.schemas import (
    ForgotPasswordBody,
    PasswordChangeBody,
    ProfileUpdateBody,
    ResetPasswordBody,
    VerifyResetCodeBody,
)
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.presentation.chatbot_rate_limit import ChatbotRateLimiter

auth_rate_limiter = ChatbotRateLimiter(max_per_minute=20)


def _rate_limit(request: Request, bucket: str, identity: str, limit: int) -> str:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{bucket}:{client_ip}:{identity.lower().strip()}"
    retry_after = auth_rate_limiter.check(key, limit)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de tentatives",
            headers={"Retry-After": str(retry_after)},
        )
    return key


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    firstName: str = Field(min_length=1, max_length=128)
    lastName: str = Field(min_length=1, max_length=128)
    organizationName: str = Field(min_length=1, max_length=255)


class RefreshRequest(BaseModel):
    refreshToken: str | None = Field(default=None, min_length=20)


class AuthResponse(BaseModel):
    user: dict
    token: str
    refreshToken: str


REFRESH_COOKIE = "aibos_refresh"


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    from app.core.config import settings

    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=settings.refresh_token_exp_days * 86400,
        httponly=True,
        secure=settings.is_production,
        samesite="none" if settings.is_production else "lax",
        path="/api/v1/auth",
    )


def build_auth_router(auth_service: AuthService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

    @router.post("/login", response_model=AuthResponse)
    def login(payload: LoginRequest, request: Request, response: Response):
        rate_key = _rate_limit(request, "login", str(payload.email), 10)
        token, refresh_token = auth_service.login(payload.email, payload.password)
        auth_rate_limiter.reset_key(rate_key)
        set_refresh_cookie(response, refresh_token)
        user = auth_service.me_from_access_token(token)
        return AuthResponse(user=user, token=token, refreshToken=refresh_token)

    @router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
    def register(payload: RegisterRequest, request: Request, response: Response):
        _rate_limit(request, "register", str(payload.email), 5)
        token, refresh_token = auth_service.register(
            email=str(payload.email),
            password=payload.password,
            first_name=payload.firstName,
            last_name=payload.lastName,
            organization_name=payload.organizationName,
        )
        set_refresh_cookie(response, refresh_token)
        user = auth_service.me_from_access_token(token)
        return AuthResponse(user=user, token=token, refreshToken=refresh_token)

    @router.post("/refresh", response_model=AuthResponse)
    def refresh(request: Request, response: Response, payload: RefreshRequest | None = None):
        presented = (payload.refreshToken if payload else None) or request.cookies.get(REFRESH_COOKIE)
        if not presented:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token requis")
        token, refresh_token = auth_service.refresh(presented)
        set_refresh_cookie(response, refresh_token)
        user = auth_service.me_from_access_token(token)
        return AuthResponse(user=user, token=token, refreshToken=refresh_token)

    @router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
    def logout(request: Request, response: Response, payload: RefreshRequest | None = None) -> None:
        presented = (payload.refreshToken if payload else None) or request.cookies.get(REFRESH_COOKIE)
        if presented:
            auth_service.logout(presented)
        response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")

    @router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
    def logout_all(response: Response, claims: dict = Depends(require_auth)) -> None:
        auth_service.logout_all(claims)
        response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")

    @router.post("/forgot-password")
    def forgot_password(body: ForgotPasswordBody, request: Request) -> dict:
        _rate_limit(request, "forgot-password", str(body.email), 5)
        auth_service.request_password_reset(str(body.email))
        return {
            "status": "ok",
            "message": "Si ce compte existe, un code de vérification a été envoyé.",
        }

    @router.post("/verify-reset-code")
    def verify_reset_code(body: VerifyResetCodeBody) -> dict:
        auth_service.verify_reset_code(str(body.email), body.code)
        return {"status": "ok"}

    @router.post("/reset-password")
    def reset_password(body: ResetPasswordBody) -> dict:
        auth_service.reset_password(str(body.email), body.code, body.newPassword)
        return {"status": "ok"}

    @router.get("/me")
    def me(claims: dict = Depends(require_auth)):
        return auth_service.me_from_claims(claims)

    @router.patch("/me")
    def update_me(
        body: ProfileUpdateBody,
        db: Session = Depends(get_tenant_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        user = UserRepository(db).get_by_id(claims_user_id(claims))
        if not user or not user.active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
        UserRepository(db).update_profile(user, first_name=body.firstName, last_name=body.lastName)
        db.commit()
        db.refresh(user)
        return auth_service._user_to_me(user)

    @router.post("/change-password")
    def change_password(
        body: PasswordChangeBody,
        db: Session = Depends(get_tenant_db),
        claims: dict = Depends(require_auth),
    ) -> dict:
        user = UserRepository(db).get_by_id(claims_user_id(claims))
        if not user or not user.active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
        if not verify_password(body.currentPassword, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe actuel incorrect")
        UserRepository(db).update_password(user, hash_password(body.newPassword))
        db.commit()
        return {"status": "ok"}

    return router
