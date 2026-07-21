from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage


logger = logging.getLogger("aibos.email")


@dataclass(frozen=True)
class EmailDelivery:
    recipient: str
    subject: str
    text: str


class EmailService:
    """Send transactional emails through SMTP or a development log outbox."""

    def __init__(
        self,
        *,
        mode: str = "log",
        smtp_host: str | None = None,
        smtp_port: int = 587,
        smtp_use_tls: bool = True,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        sender: str = "AI BOS <noreply@aibos.local>",
    ) -> None:
        self.mode = mode.lower().strip()
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_use_tls = smtp_use_tls
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.sender = sender
        self.outbox: list[EmailDelivery] = []

        if self.mode not in {"log", "smtp"}:
            raise ValueError("EMAIL_MODE doit être 'log' ou 'smtp'")
        if self.mode == "smtp" and not self.smtp_host:
            raise ValueError("SMTP_HOST est requis lorsque EMAIL_MODE=smtp")

    def send_password_reset(self, *, recipient: str, code: str, expires_minutes: int) -> None:
        self._send(
            recipient=recipient,
            subject="Votre code de réinitialisation AI BOS",
            text=(
                "Une demande de réinitialisation a été reçue pour votre compte AI BOS.\n\n"
                f"Votre code de vérification : {code}\n\n"
                "Saisissez ce code sur la page de réinitialisation pour choisir un nouveau mot de passe.\n"
                f"Ce code expire dans {expires_minutes} minutes et ne peut être utilisé qu'une fois.\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
            ),
        )

    def send_invitation(
        self,
        *,
        recipient: str,
        invitation_url: str,
        invited_by_name: str,
        message: str | None = None,
    ) -> None:
        extra = f"\n\nMessage : {message}" if message else ""
        self._send(
            recipient=recipient,
            subject="Vous êtes invité sur AI BOS",
            text=(
                f"{invited_by_name} vous invite à rejoindre son espace AI BOS.\n\n"
                f"Accepter l'invitation : {invitation_url}{extra}\n\n"
                "Ce lien est personnel. Ne le partagez pas."
            ),
        )

    def _send(self, *, recipient: str, subject: str, text: str) -> None:
        delivery = EmailDelivery(recipient=recipient, subject=subject, text=text)
        if self.mode == "log":
            self.outbox.append(delivery)
            logger.info("email_logged recipient=%s subject=%s\n%s", recipient, subject, text)
            return

        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(text)

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as smtp:
            if self.smtp_use_tls:
                smtp.starttls()
            if self.smtp_user:
                smtp.login(self.smtp_user, self.smtp_password or "")
            smtp.send_message(message)
