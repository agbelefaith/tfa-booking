"""The shapes of data the API sends out (and later, receives). what the customer sees filter of models.py dont need the customers seeing internal information like is_active ect"""
from datetime import date, datetime, time

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field, model_validator


class ServiceOut(BaseModel):
    """A service, as shown to clients on the booking page."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration_minutes: int
    price_cents: int
    allows_nail_art: bool


class AddOnOut(BaseModel):
    """Add ons, shown to clients on the booking page."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    extra_minutes: int
    price_cents: int
    is_nail_art: bool


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


class CheckoutOut(BaseModel):
    """Where to send the client to pay their deposit."""

    checkout_url: str


class BookingCreated(BookingOut):
    """Returned once, right after booking. The token lets the client manage it."""

    manage_token: str


class CancelRequest(BaseModel):
    """What a client sends to cancel their own booking."""

    token: str


class AdminBookingOut(BaseModel):
    """A booking as you see it in your dashboard (with the client's details)."""

    id: int
    status: str
    starts_at: datetime
    ends_at: datetime
    total_cents: int
    deposit_cents: int
    service_name: str
    add_on_names: list[str]
    customer_name: str
    customer_email: str
    customer_phone: str


class OpeningHours(BaseModel):
    """One block of opening hours, e.g. Saturday 10:00-18:00."""

    model_config = ConfigDict(from_attributes=True)

    day_of_week: int = Field(ge=0, le=6)  # 0 = Monday ... 6 = Sunday
    opens_at: time
    closes_at: time

    @model_validator(mode="after")
    def closes_after_opening(self):
        if self.closes_at <= self.opens_at:
            raise ValueError("Closing time must be after opening time")
        return self


class TimeOffCreate(BaseModel):
    """Days off, e.g. 24 Dec to 2 Jan (both days included)."""

    first_day: date
    last_day: date
    reason: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def last_day_not_before_first(self):
        if self.last_day < self.first_day:
            raise ValueError("Last day can't be before the first day")
        return self


class TimeOffOut(BaseModel):
    """A block of time off, as stored."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    starts_at: datetime
    ends_at: datetime
    reason: str | None


class BookingPolicyOut(BaseModel):
    """Booking rules the website needs to show prices correctly."""

    deposit_cents: int
