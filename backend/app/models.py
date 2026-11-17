"""Database tables, written as Python classes."""
from datetime import datetime
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
