"""Lot B models: sales orders, campaigns, projects, calendar events, meetings.

Date fields are stored as ISO strings to keep the exact API format the
frontend already consumes (YYYY-MM-DD or full ISO datetimes).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SalesOrder(Base):
    __tablename__ = "sales_orders"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    order_number: Mapped[str] = mapped_column(String(32), nullable=False)
    customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="EUR")
    date: Mapped[str] = mapped_column(String(32), nullable=False)
    sales_rep_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sales_rep_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    line_items: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="email")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    reach: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    click_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    conversions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    budget: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    spent: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    start_date: Mapped[str] = mapped_column(String(32), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="planning")
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    start_date: Mapped[str] = mapped_column(String(32), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    budget: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    spent: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    team_members: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#4f46e5")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="meeting")
    start_date: Mapped[str] = mapped_column(String(40), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(40), nullable=True)
    color: Mapped[str] = mapped_column(String(16), nullable=False, default="#4f46e5")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attendees: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    org_id: Mapped[str] = mapped_column(String(64), ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[str] = mapped_column(String(32), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="upcoming")
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attendees: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    agenda: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_items: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
