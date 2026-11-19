"""Your side of the system: everything under /admin needs the admin key."""
import secrets
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import payments
from app.config import settings
from app.db import get_db
from app.models import (
    ACTIVE_STATUSES,
    AddOn,
    Booking,
    BookingAddOn,
    Customer,
    Service,
    TimeOff,
    WeeklyHours,
)
from app.schemas import AdminBookingOut, BookingOut, OpeningHours, TimeOffCreate, TimeOffOut


def require_admin(x_admin_key: str = Header(default="")):
    """Only you (with the admin key) can use admin endpoints."""
    if not settings.admin_api_key or not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Admin key required")


# Every endpoint in this file starts with /admin and checks the key first.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/check")
def check_admin_key():
    """Lets the dashboard check the key is right before showing anything."""
    return {"ok": True}


# ---------- Bookings ----------

@router.get("/bookings", response_model=list[AdminBookingOut])
def list_bookings(start: date, end: date, db: Session = Depends(get_db)):
    """Every booking from `start` up to (not including) `end`, in time order."""
    timezone = ZoneInfo(settings.business_timezone)
    rows = db.execute(
        select(Booking, Service.name, Customer)
        .join(Service, Booking.service_id == Service.id)
        .join(Customer, Booking.customer_id == Customer.id)
        .where(
            Booking.starts_at >= datetime.combine(start, time.min, tzinfo=timezone),
            Booking.starts_at < datetime.combine(end, time.min, tzinfo=timezone),
        )
        .order_by(Booking.starts_at)
    ).all()

    # Add-on names for all these bookings, in one query
    booking_ids = [booking.id for booking, _, _ in rows]
    add_on_rows = db.execute(
        select(BookingAddOn.booking_id, AddOn.name)
        .join(AddOn, BookingAddOn.add_on_id == AddOn.id)
        .where(BookingAddOn.booking_id.in_(booking_ids))
    ).all()
    add_ons_by_booking = {}
    for booking_id, name in add_on_rows:
        add_ons_by_booking.setdefault(booking_id, []).append(name)

    return [
        AdminBookingOut(
            id=booking.id,
            status=booking.status,
            starts_at=booking.starts_at,
            ends_at=booking.ends_at,
            total_cents=booking.total_cents,
            deposit_cents=booking.deposit_cents,
            service_name=service_name,
            add_on_names=add_ons_by_booking.get(booking.id, []),
            customer_name=customer.name,
            customer_email=customer.email,
            customer_phone=customer.phone,
        )
        for booking, service_name, customer in rows
    ]


@router.post("/bookings/{booking_id}/cancel", response_model=BookingOut)
def business_cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    """You have to cancel (sick, emergency): the client gets their deposit back."""
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=409, detail="This booking can't be cancelled")

    if booking.status == "confirmed" and booking.stripe_payment_intent_id:
        refund = payments.refund_deposit(booking.id, booking.stripe_payment_intent_id)
        booking.stripe_refund_id = refund.id
    elif booking.stripe_checkout_session_id:
        payments.expire_checkout(booking.stripe_checkout_session_id)

    booking.status = "business_cancelled"
    db.commit()
    return booking


@router.post("/bookings/{booking_id}/no-show", response_model=BookingOut)
def mark_no_show(booking_id: int, db: Session = Depends(get_db)):
    """The client didn't turn up. You keep the deposit."""
    return set_final_status(db, booking_id, "no_show")


@router.post("/bookings/{booking_id}/complete", response_model=BookingOut)
def mark_completed(booking_id: int, db: Session = Depends(get_db)):
    """The appointment happened."""
    return set_final_status(db, booking_id, "completed")


def set_final_status(db: Session, booking_id: int, status: str) -> Booking:
    """Close off a confirmed booking once its start time has passed."""
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "confirmed":
        raise HTTPException(status_code=409, detail="Only confirmed bookings can be closed off")
    if booking.starts_at > datetime.now(booking.starts_at.tzinfo):
        raise HTTPException(status_code=409, detail="This appointment hasn't started yet")
    booking.status = status
    db.commit()
    return booking


# ---------- Opening hours ----------

@router.get("/opening-hours", response_model=list[OpeningHours])
def get_opening_hours(db: Session = Depends(get_db)):
    """Your weekly opening hours."""
    return db.scalars(
        select(WeeklyHours).order_by(WeeklyHours.day_of_week, WeeklyHours.opens_at)
    ).all()


@router.put("/opening-hours", response_model=list[OpeningHours])
def replace_opening_hours(hours: list[OpeningHours], db: Session = Depends(get_db)):
    """Save your whole week in one go (replaces what was there)."""
    db.execute(delete(WeeklyHours))
    db.add_all(WeeklyHours(**block.model_dump()) for block in hours)
    db.commit()
    return get_opening_hours(db)


# ---------- Time off ----------

@router.get("/time-off", response_model=list[TimeOffOut])
def list_time_off(db: Session = Depends(get_db)):
    """Upcoming time off, soonest first."""
    now = datetime.now(ZoneInfo(settings.business_timezone))
    return db.scalars(
        select(TimeOff).where(TimeOff.ends_at > now).order_by(TimeOff.starts_at)
    ).all()


@router.post("/time-off", response_model=TimeOffOut, status_code=201)
def add_time_off(request: TimeOffCreate, db: Session = Depends(get_db)):
    """Block out whole days, from the start of the first day to the end of the last."""
    timezone = ZoneInfo(settings.business_timezone)
    time_off = TimeOff(
        starts_at=datetime.combine(request.first_day, time.min, tzinfo=timezone),
        ends_at=datetime.combine(request.last_day + timedelta(days=1), time.min, tzinfo=timezone),
        reason=request.reason,
    )
    db.add(time_off)
    db.commit()
    return time_off


@router.delete("/time-off/{time_off_id}", status_code=204)
def remove_time_off(time_off_id: int, db: Session = Depends(get_db)):
    """Delete a block of time off."""
    time_off = db.get(TimeOff, time_off_id)
    if time_off is None:
        raise HTTPException(status_code=404, detail="Time off not found")
    db.delete(time_off)
    db.commit()
