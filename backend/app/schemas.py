"""The shapes of data the API sends out (and later, receives). what the customer sees filter of models.py dont need the customers seeing internal information like is_active ect"""
from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field


class ServiceOut(BaseModel):
    """A service, as shown to clients on the booking page."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration_minutes: int
    price_cents: int
    deposit_cents: int


class AddOnOut(BaseModel):
    """Add ons, shown to clients on the booking page."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    extra_minutes: int
    price_cents: int


class BookingCreate(BaseModel):
    """What the booking page sends when a client books."""

    service_id: int
    add_on_ids: list[int] = []
    starts_at: AwareDatetime
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=6, max_length=20)


class BookingOut(BaseModel):
    """What the client gets back after booking."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    starts_at: datetime
    ends_at: datetime
    total_cents: int
    deposit_cents: int
