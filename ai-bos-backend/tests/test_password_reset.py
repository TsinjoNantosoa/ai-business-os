from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app, email_service
from app.services.email_service import EmailService


client = TestClient(app)


@pytest.fixture(autouse=True)
def _email_log_mode():
    """Capture emails in the outbox even when .env configures real SMTP."""
    previous_mode = email_service.mode
    email_service.mode = "log"
    yield
    email_service.mode = previous_mode
    email_service.outbox.clear()


def _last_reset_code() -> str:
    delivery = email_service.outbox[-1]
    match = re.search(r"code de vérification : (\d{6})", delivery.text)
    assert match, delivery.text
    return match.group(1)


def test_forgot_password_does_not_reveal_account_existence() -> None:
    email_service.outbox.clear()

    known = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "sales@demo.aibos.io"},
    )
    assert known.status_code == 200
    assert known.json()["status"] == "ok"
    assert len(email_service.outbox) == 1

    unknown = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "unknown@example.com"},
    )
    assert unknown.status_code == 200
    assert unknown.json() == known.json()
    assert len(email_service.outbox) == 1


def test_verify_reset_code_validates_without_consuming() -> None:
    email = "sales@demo.aibos.io"
    email_service.outbox.clear()
    client.post("/api/v1/auth/forgot-password", json={"email": email})
    code = _last_reset_code()

    wrong = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": email, "code": "000000" if code != "000000" else "111111"},
    )
    assert wrong.status_code == 400

    valid = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": email, "code": code},
    )
    assert valid.status_code == 200

    # Verification does not consume the code: it can be verified again.
    again = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": email, "code": code},
    )
    assert again.status_code == 200

    unknown = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": "unknown@example.com", "code": code},
    )
    assert unknown.status_code == 400


def test_reset_password_is_one_use_and_revokes_refresh_sessions() -> None:
    email = "sales@demo.aibos.io"
    original_password = "demo1234"
    temporary_password = "temporary99"

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": original_password},
    )
    assert login.status_code == 200
    old_refresh_token = login.json()["refreshToken"]

    email_service.outbox.clear()
    forgot = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert forgot.status_code == 200
    code = _last_reset_code()

    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "code": code, "newPassword": temporary_password},
    )
    assert reset.status_code == 200

    reused = client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "code": code, "newPassword": "another99"},
    )
    assert reused.status_code == 400

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": original_password},
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": temporary_password},
    )
    assert new_login.status_code == 200

    old_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refreshToken": old_refresh_token},
    )
    assert old_refresh.status_code == 401

    # Restore the seeded password so this test stays isolated.
    email_service.outbox.clear()
    client.post("/api/v1/auth/forgot-password", json={"email": email})
    restore_code = _last_reset_code()
    restored = client.post(
        "/api/v1/auth/reset-password",
        json={"email": email, "code": restore_code, "newPassword": original_password},
    )
    assert restored.status_code == 200


def test_reset_code_locks_after_too_many_failed_attempts() -> None:
    email = "sales@demo.aibos.io"
    email_service.outbox.clear()
    client.post("/api/v1/auth/forgot-password", json={"email": email})
    code = _last_reset_code()
    wrong_code = "000000" if code != "000000" else "111111"

    for _ in range(5):
        attempt = client.post(
            "/api/v1/auth/verify-reset-code",
            json={"email": email, "code": wrong_code},
        )
        assert attempt.status_code == 400

    # After 5 failed attempts the correct code is rejected too.
    locked = client.post(
        "/api/v1/auth/verify-reset-code",
        json={"email": email, "code": code},
    )
    assert locked.status_code == 400


def test_email_service_log_mode_builds_reset_and_invitation_messages() -> None:
    service = EmailService(mode="log")
    service.send_password_reset(
        recipient="user@example.com",
        code="123456",
        expires_minutes=60,
    )
    service.send_invitation(
        recipient="invitee@example.com",
        invitation_url="http://localhost:5173/onboarding?token=invite",
        invited_by_name="Jean Bernard",
        message="Bienvenue",
    )

    assert len(service.outbox) == 2
    assert "123456" in service.outbox[0].text
    assert "token=invite" in service.outbox[1].text
    assert service.outbox[1].recipient == "invitee@example.com"
