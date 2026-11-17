"""Database tables, written as Python classes."""
from datetime import datetime, time
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, func

from app.db import Base


class Service(Base):
    """A treatment you offer, e.g. Gel nails."""

    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    duration_minutes: Mapped[int]
    buffer_minutes: Mapped[int] = mapped_column(default=0)
    price_cents: Mapped[int]
    deposit_cents: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)


class AddOn(Base):
    """An add on, e.g nail art, removal"""

    __tablename__ = "add_ons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    extra_minutes: Mapped[int]
    price_cents: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)


class Customer(Base):
    """Someone who has booked, recognised by email."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str] = mapped_column(String(20))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(50), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WeeklyHours(Base):
    """opening hours of the business"""

    __tablename__ = "weekly_hours"

    id: Mapped[int] = mapped_column(primary_key=True)
    day_of_week: Mapped[int]
    opens_at: Mapped[time]
    closes_at: Mapped[time]


class TimeOff(Base):
    """Holidays or days off when you can't be booked."""

    __tablename__ = "time_off"

    id: Mapped[int] = mapped_column(primary_key=True)
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )
    reason: Mapped[str | None] = mapped_column(String(200))