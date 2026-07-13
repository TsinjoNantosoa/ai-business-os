from __future__ import annotations

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FeatureFlag(Base):
    """Global catalog of feature flags."""

    __tablename__ = "feature_flags"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    env: Mapped[str] = mapped_column(String(32), nullable=False, default="production")
    default_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class TenantFeatureOverride(Base):
    """Per-tenant override of a feature flag."""

    __tablename__ = "tenant_feature_overrides"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    flag_key: Mapped[str] = mapped_column(String(64), ForeignKey("feature_flags.key"), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    updated_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
