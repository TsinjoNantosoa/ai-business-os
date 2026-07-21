"""Diagnostic one-shot: verify SMTP credentials from .env."""

from app.core.config import settings
from app.services.email_service import EmailService

print(f"mode={settings.email_mode} host={settings.smtp_host} port={settings.smtp_port}")
print(f"user={settings.smtp_user} password_len={len(settings.smtp_password or '')}")

service = EmailService(
    mode=settings.email_mode,
    smtp_host=settings.smtp_host,
    smtp_port=settings.smtp_port,
    smtp_use_tls=settings.smtp_use_tls,
    smtp_user=settings.smtp_user,
    smtp_password=settings.smtp_password,
    sender=settings.smtp_from,
)

try:
    service.send_password_reset(
        recipient=settings.smtp_user or "",
        code="123456",
        expires_minutes=60,
    )
    print("SMTP OK — email envoyé")
except Exception as exc:
    print(f"SMTP FAIL — {type(exc).__name__}: {exc}")
