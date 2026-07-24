from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organization import Organization


class OrganizationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self) -> list[Organization]:
        return list(self._session.scalars(select(Organization).order_by(Organization.name)).all())

    def get_by_id(self, org_id: str) -> Organization | None:
        return self._session.get(Organization, org_id)

    def create(
        self,
        *,
        org_id: str,
        name: str,
        plan: str = "starter",
        currency: str = "EUR",
        timezone: str = "Europe/Paris",
        locale: str = "fr",
    ) -> Organization:
        org = Organization(
            id=org_id,
            name=name.strip(),
            plan=plan,
            currency=currency,
            timezone=timezone,
            locale=locale,
        )
        self._session.add(org)
        self._session.flush()
        return org

    def count(self) -> int:
        return len(self.list_all())

    def update(
        self,
        org: Organization,
        *,
        name: str | None = None,
        currency: str | None = None,
        timezone: str | None = None,
        locale: str | None = None,
        address: str | None = None,
    ) -> Organization:
        if name is not None:
            org.name = name
        if currency is not None:
            org.currency = currency
        if timezone is not None:
            org.timezone = timezone
        if locale is not None:
            org.locale = locale
        if address is not None:
            org.address = address
        self._session.commit()
        self._session.refresh(org)
        return org
