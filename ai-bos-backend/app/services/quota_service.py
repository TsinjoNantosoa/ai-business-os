"""S35 — hard quotas by billing plan (RPM + monthly AI tokens + seats)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_observability import AiTrace
from app.models.billing import BillingPlan, Subscription
from app.presentation.chatbot_rate_limit import ChatbotRateLimiter
from app.repositories.billing_repository import BillingRepository
from app.repositories.user_repository import UserRepository

# Shared limiter instance (org-scoped keys) — separate from global chatbot limiter defaults
_plan_rpm_limiter = ChatbotRateLimiter(max_per_minute=60)


@dataclass(frozen=True)
class QuotaSnapshot:
    plan_code: str
    plan_name: str
    ai_rpm: int
    ai_tokens_used: int
    ai_tokens_limit: int
    seats_used: int
    seats_limit: int
    storage_gb_used: int
    storage_gb_limit: int
    period_start: datetime | None
    period_end: datetime | None

    @property
    def tokens_remaining(self) -> int:
        return max(0, self.ai_tokens_limit - self.ai_tokens_used)

    @property
    def tokens_exhausted(self) -> bool:
        return self.ai_tokens_used >= self.ai_tokens_limit > 0

    def to_dict(self) -> dict:
        return {
            "planCode": self.plan_code,
            "planName": self.plan_name,
            "aiRpm": self.ai_rpm,
            "periodStart": self.period_start.isoformat() if self.period_start else None,
            "periodEnd": self.period_end.isoformat() if self.period_end else None,
            "usage": {
                "seats": {"used": self.seats_used, "limit": self.seats_limit},
                "aiTokens": {"used": self.ai_tokens_used, "limit": self.ai_tokens_limit},
                "storageGb": {"used": self.storage_gb_used, "limit": self.storage_gb_limit},
            },
            "tokensRemaining": self.tokens_remaining,
            "tokensExhausted": self.tokens_exhausted,
        }


def period_ai_tokens_used(db: Session, org_id: str, period_start: datetime, period_end: datetime) -> int:
    stmt = (
        select(func.coalesce(func.sum(AiTrace.input_tokens + AiTrace.output_tokens), 0))
        .where(
            AiTrace.org_id == org_id,
            AiTrace.created_at >= period_start,
            AiTrace.created_at <= period_end,
        )
    )
    return int(db.scalars(stmt).first() or 0)


def get_quota_snapshot(db: Session, org_id: str) -> QuotaSnapshot | None:
    sub = BillingRepository(db).get_subscription_for_org(org_id)
    if not sub or not sub.plan:
        return None
    plan: BillingPlan = sub.plan
    seats_used = sub.seats_used
    try:
        seats_used = len(UserRepository(db).list_by_org(org_id))
    except Exception:
        pass

    tokens_used = period_ai_tokens_used(db, org_id, sub.current_period_start, sub.current_period_end)
    # Keep subscription meter in sync for billing UI
    sub.ai_tokens_used = tokens_used
    sub.seats_used = seats_used

    return QuotaSnapshot(
        plan_code=plan.code,
        plan_name=plan.name,
        ai_rpm=int(getattr(plan, "ai_rpm", None) or 20),
        ai_tokens_used=tokens_used,
        ai_tokens_limit=int(plan.ai_tokens_limit),
        seats_used=seats_used,
        seats_limit=int(plan.seats_limit),
        storage_gb_used=int(sub.storage_gb_used),
        storage_gb_limit=int(plan.storage_gb_limit),
        period_start=sub.current_period_start,
        period_end=sub.current_period_end,
    )


def enforce_ai_chat_quota(db: Session, *, org_id: str, rate_key: str) -> QuotaSnapshot | None:
    """Raise 429 if plan RPM or monthly token quota exceeded. Returns snapshot when available."""
    snapshot = get_quota_snapshot(db, org_id)
    rpm = snapshot.ai_rpm if snapshot else 20
    retry = _plan_rpm_limiter.check(f"ai:{org_id}:{rate_key}", max_per_minute=rpm)
    if retry is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Limite plan dépassée : {rpm} requêtes IA / minute "
                f"({snapshot.plan_name if snapshot else 'default'}). Réessayez dans {retry}s."
            ),
            headers={"Retry-After": str(retry)},
        )

    if snapshot and snapshot.tokens_exhausted:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Quota tokens IA épuisé pour le plan {snapshot.plan_name} "
                f"({snapshot.ai_tokens_used}/{snapshot.ai_tokens_limit}). "
                "Passez à un plan supérieur dans Paramètres → Facturation."
            ),
            headers={"Retry-After": "3600"},
        )
    return snapshot


def enforce_seat_quota(db: Session, org_id: str) -> None:
    snapshot = get_quota_snapshot(db, org_id)
    if not snapshot:
        return
    if snapshot.seats_used >= snapshot.seats_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Limite de sièges atteinte ({snapshot.seats_used}/{snapshot.seats_limit}) "
                f"pour le plan {snapshot.plan_name}."
            ),
        )


def reset_plan_rpm_limiter() -> None:
    _plan_rpm_limiter.reset()
