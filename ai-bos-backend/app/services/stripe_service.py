from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any

from app.core.config import settings


class StripeService:
    """Stripe sandbox integration with mock fallback when keys are absent."""

    def __init__(self) -> None:
        try:
            import stripe
            self._stripe = stripe
            if settings.stripe_secret_key:
                stripe.api_key = settings.stripe_secret_key
        except ImportError:
            self._stripe = None

    @property
    def is_live(self) -> bool:
        return self._stripe is not None

    def create_checkout_session(
        self,
        *,
        org_id: str,
        plan_code: str,
        customer_email: str,
        price_amount: int,
        currency: str,
        stripe_price_id: str | None,
    ) -> dict[str, str]:
        if self._stripe and settings.stripe_secret_key and stripe_price_id:
            session = self._stripe.checkout.Session.create(
                mode="subscription",
                customer_email=customer_email,
                line_items=[{"price": stripe_price_id, "quantity": 1}],
                success_url=f"{settings.app_public_url}/app/settings/billing?checkout=success",
                cancel_url=f"{settings.app_public_url}/app/settings/billing?checkout=cancel",
                metadata={"org_id": org_id, "plan_code": plan_code},
            )
            return {"sessionId": session.id, "checkoutUrl": session.url or ""}

        session_id = f"cs_test_{secrets.token_hex(8)}"
        checkout_url = (
            f"{settings.app_public_url}/app/settings/billing"
            f"?checkout=mock&session_id={session_id}&plan={plan_code}"
        )
        return {"sessionId": session_id, "checkoutUrl": checkout_url}

    def verify_webhook(self, payload: bytes, signature_header: str | None) -> dict[str, Any]:
        if settings.stripe_webhook_secret:
            if not signature_header:
                raise ValueError("Missing Stripe-Signature")
            if not self._stripe:
                raise RuntimeError("stripe package is required for webhook verification")
            event = self._stripe.Webhook.construct_event(
                payload, signature_header, settings.stripe_webhook_secret
            )
            return event
        if settings.is_production or not settings.allow_unsigned_stripe_webhooks:
            raise ValueError("Stripe webhook verification is not configured")
        return json.loads(payload.decode("utf-8"))
