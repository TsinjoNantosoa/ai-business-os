from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.feature_flag import FeatureFlag, TenantFeatureOverride


class FeatureFlagRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_flags(self) -> list[FeatureFlag]:
        return list(self._session.scalars(select(FeatureFlag).order_by(FeatureFlag.key)).all())

    def get_flag(self, key: str) -> FeatureFlag | None:
        return self._session.get(FeatureFlag, key)

    def count_flags(self) -> int:
        return len(self.list_flags())

    def list_overrides_for_org(self, org_id: str) -> list[TenantFeatureOverride]:
        stmt = select(TenantFeatureOverride).where(TenantFeatureOverride.org_id == org_id)
        return list(self._session.scalars(stmt).all())

    def get_override(self, org_id: str, flag_key: str) -> TenantFeatureOverride | None:
        stmt = (
            select(TenantFeatureOverride)
            .where(TenantFeatureOverride.org_id == org_id)
            .where(TenantFeatureOverride.flag_key == flag_key)
        )
        return self._session.scalars(stmt).first()

    def upsert_override(
        self,
        *,
        org_id: str,
        flag_key: str,
        enabled: bool,
        updated_by: str | None,
    ) -> TenantFeatureOverride:
        existing = self.get_override(org_id, flag_key)
        if existing:
            existing.enabled = enabled
            existing.updated_by = updated_by
            self._session.commit()
            self._session.refresh(existing)
            return existing

        row = TenantFeatureOverride(
            id=f"ffo-{secrets.token_hex(8)}",
            org_id=org_id,
            flag_key=flag_key,
            enabled=enabled,
            updated_by=updated_by,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return row

    def delete_override(self, org_id: str, flag_key: str) -> bool:
        existing = self.get_override(org_id, flag_key)
        if not existing:
            return False
        self._session.delete(existing)
        self._session.commit()
        return True
