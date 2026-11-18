"""Entry point for the FastAPI backend."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.availability import find_free_slots
from app.config import settings
from app.db import get_db
from app.models import AddOn, Booking, Service, TimeOff, WeeklyHours
from app.schemas import AddOnOut, ServiceOut

app = FastAPI(title=settings.app_name)

# Booking statuses that take up time in the calendar.
ACTIVE_STATUSES = ("pending", "confirmed")


@app.get("/health")
def health_check() -> dict:
    """Simple endpoint to confirm the API is running."""
    return {"status": "ok", "environment": settings.environment}


@app.get("/services", response_model=list[ServiceOut])
def list_services(db: Session = Depends(get_db)):
    """All services clients can book, cheapest first."""
    query = select(Service).where(Service.is_active).order_by(Service.price_cents)
    return db.scalars(query).all()


@app.get("/add-ons",response_model=list[AddOnOut])
def list_add_ons(db: Session = Depends(get_db)):
    """All add ons clients can add to their bookings."""
    query = select(AddOn).where(AddOn.is_active).order_by(AddOn.price_cents)
    return db.scalars(query).all()


@app.get("/availability", response_model=list[datetime])
def get_availability(
    day: date,
    service_id: int,
    add_on_ids: list[int] = Query(default=[]),
    db: Session = Depends(get_db),
):
    """Free start times on a day, for a service plus any add-ons."""
    # 1. What are they booking, and how long will it take?
    service = db.get(Service, service_id)
    if service is None or not service.is_active:
        raise HTTPException(status_code=404, detail="Service not found")

    add_ons = db.scalars(
        select(AddOn).where(AddOn.id.in_(add_on_ids), AddOn.is_active)
    ).all()
    if len(add_ons) != len(set(add_on_ids)):
        raise HTTPException(status_code=404, detail="Add-on not found")

    appointment_minutes = service.duration_minutes + sum(a.extra_minutes for a in add_ons)

    # 2. When are you open that day?
    hours = db.scalars(
        select(WeeklyHours).where(WeeklyHours.day_of_week == day.weekday())
    ).all()
    opening_hours = [(h.opens_at, h.closes_at) for h in hours]

    # 3. What's already taken that day? (bookings + time off)
    timezone = ZoneInfo(settings.business_timezone)
    day_start = datetime.combine(day, time.min, tzinfo=timezone)
    day_end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=timezone)

    bookings = db.scalars(
        select(Booking).where(
            Booking.status.in_(ACTIVE_STATUSES),
            Booking.starts_at < day_end,
            Booking.blocked_until > day_start,
        )
    ).all()
    time_off = db.scalars(
        select(TimeOff).where(TimeOff.starts_at < day_end, TimeOff.ends_at > day_start)
    ).all()
    busy = [(b.starts_at, b.blocked_until) for b in bookings]
    busy += [(t.starts_at, t.ends_at) for t in time_off]

    # 4. Let the slot calculator do the maths.
    return find_free_slots(
        day,
        opening_hours,
        busy,
        appointment_minutes,
        service.buffer_minutes,
        timezone,
        now=datetime.now(timezone),
    )
