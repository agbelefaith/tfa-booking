"""Entry point for the FastAPI backend."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.availability import find_free_slots
from app.config import settings
from app.db import get_db
from app.models import AddOn, Booking, BookingAddOn, Customer, Service, TimeOff, WeeklyHours
from app.schemas import AddOnOut, BookingCreate, BookingOut, ServiceOut

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


def load_service_and_add_ons(db: Session, service_id: int, add_on_ids: list[int]):
    """Fetch what's being booked, or stop with a 404."""
    service = db.get(Service, service_id)
    if service is None or not service.is_active:
        raise HTTPException(status_code=404, detail="Service not found")

    add_ons = db.scalars(
        select(AddOn).where(AddOn.id.in_(add_on_ids), AddOn.is_active)
    ).all()
    if len(add_ons) != len(set(add_on_ids)):
        raise HTTPException(status_code=404, detail="Add-on not found")

    return service, add_ons


def free_slots_for(db: Session, day: date, service: Service, add_ons: list[AddOn]) -> list[datetime]:
    """Every free start time on `day` for this service + add-ons."""
    appointment_minutes = service.duration_minutes + sum(a.extra_minutes for a in add_ons)

    # When are you open that day?
    hours = db.scalars(
        select(WeeklyHours).where(WeeklyHours.day_of_week == day.weekday())
    ).all()
    opening_hours = [(h.opens_at, h.closes_at) for h in hours]

    # What's already taken that day? (bookings + time off)
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

    return find_free_slots(
        day,
        opening_hours,
        busy,
        appointment_minutes,
        service.buffer_minutes,
        timezone,
        now=datetime.now(timezone),
    )


@app.get("/availability", response_model=list[datetime])
def get_availability(
    day: date,
    service_id: int,
    add_on_ids: list[int] = Query(default=[]),
    db: Session = Depends(get_db),
):
    """Free start times on a day, for a service plus any add-ons."""
    service, add_ons = load_service_and_add_ons(db, service_id, add_on_ids)
    return free_slots_for(db, day, service, add_ons)


@app.post("/bookings", response_model=BookingOut, status_code=201)
def create_booking(request: BookingCreate, db: Session = Depends(get_db)):
    """Hold a slot for a client. It stays 'pending' until the deposit is paid."""
    service, add_ons = load_service_and_add_ons(db, request.service_id, request.add_on_ids)

    # 1. Is that time actually free? (never trust the browser)
    timezone = ZoneInfo(settings.business_timezone)
    starts_at = request.starts_at.astimezone(timezone)
    if starts_at not in free_slots_for(db, starts_at.date(), service, add_ons):
        raise HTTPException(status_code=409, detail="That time isn't available")

    # 2. Find the customer by email, or create them.
    email = request.email.lower()
    customer = db.scalar(select(Customer).where(Customer.email == email))
    if customer is None:
        customer = Customer(email=email, name=request.name, phone=request.phone)
        db.add(customer)
        db.flush()  # gives the new customer an id
    else:
        customer.name = request.name
        customer.phone = request.phone

    # 3. Work out times and prices (price snapshot).
    appointment_minutes = service.duration_minutes + sum(a.extra_minutes for a in add_ons)
    ends_at = starts_at + timedelta(minutes=appointment_minutes)
    booking = Booking(
        customer_id=customer.id,
        service_id=service.id,
        starts_at=starts_at,
        ends_at=ends_at,
        blocked_until=ends_at + timedelta(minutes=service.buffer_minutes),
        status="pending",
        total_cents=service.price_cents + sum(a.price_cents for a in add_ons),
        deposit_cents=service.deposit_cents,
    )
    db.add(booking)

    # 4. Save. If someone grabbed the slot a split second ago, Postgres refuses.
    try:
        db.flush()  # sends the booking to Postgres and gives it an id
        db.add_all(BookingAddOn(booking_id=booking.id, add_on_id=a.id) for a in add_ons)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="That time was just taken")

    return booking
