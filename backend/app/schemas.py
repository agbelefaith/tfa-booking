"""The shapes of data the API sends out (and later, receives). what the customer sees filter of models.py dont need the customers seeing internal information like is_active ect"""
from pydantic import BaseModel, ConfigDict


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

    

