from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.presentation.deps import claims_user_id, require_auth
from app.presentation.schemas import (
    ForgotPasswordBody,
    PasswordChangeBody,
    ProfileUpdateBody,
    ResetPasswordBody,
    VerifyResetCodeBody,
)
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


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

    @router.post("/forgot-password")
    def forgot_password(body: ForgotPasswordBody) -> dict:
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
        db: Session = Depends(get_db),
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
        db: Session = Depends(get_db),
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
