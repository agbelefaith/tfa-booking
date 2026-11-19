"""Entry point for the FastAPI backend."""
import logging
import secrets
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import stripe
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.availability import find_free_slots
from app.config import settings
from app.db import get_db
from app.models import AddOn, Booking, BookingAddOn, Customer, Service, StripeEvent, TimeOff, WeeklyHours
from app.schemas import (
    AddOnOut,
    BookingCreate,
    BookingCreated,
    BookingOut,
    CancelRequest,
    CheckoutOut,
    ServiceOut,
)
from app import payments

app = FastAPI(title=settings.app_name)

# Let the booking website (a different address) call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_methods=["*"],
    allow_headers=["*"],
)
logger = logging.getLogger("uvicorn.error")

# Booking statuses that take up time in the calendar.
ACTIVE_STATUSES = ("pending", "confirmed")

# A pending booking that never reached the payment page gets released after this.
ABANDONED_AFTER_MINUTES = 35


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


def expire_abandoned_bookings(db: Session) -> None:
    """Release slots held by bookings that never got a payment page.

    (Bookings that did get one are handled by Stripe's checkout.session.expired webhook.)
    """
    cutoff = datetime.now(ZoneInfo("UTC")) - timedelta(minutes=ABANDONED_AFTER_MINUTES)
    db.execute(
        update(Booking)
        .where(
            Booking.status == "pending",
            Booking.stripe_checkout_session_id.is_(None),
            Booking.created_at < cutoff,
        )
        .values(status="cancelled")
    )
    db.commit()


def free_slots_for(db: Session, day: date, service: Service, add_ons: list[AddOn]) -> list[datetime]:
    """Every free start time on `day` for this service + add-ons."""
    expire_abandoned_bookings(db)
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


@app.get("/opening-days", response_model=list[int])
def list_opening_days(db: Session = Depends(get_db)):
    """Weekdays you're open (0 = Monday ... 6 = Sunday), so the calendar can grey out closed days."""
    return sorted(set(db.scalars(select(WeeklyHours.day_of_week)).all()))


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


@app.post("/bookings", response_model=BookingCreated, status_code=201)
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


@app.post("/bookings/{booking_id}/checkout", response_model=CheckoutOut)
def start_deposit_checkout(booking_id: int, db: Session = Depends(get_db)):
    """Get a Stripe payment page for a pending booking's deposit."""
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != "pending":
        raise HTTPException(status_code=409, detail="This booking doesn't need a deposit")

    # Clicked "Pay" twice? Reuse the payment page that's still open.
    if booking.stripe_checkout_session_id:
        existing = payments.get_checkout(booking.stripe_checkout_session_id)
        if existing.status == "open":
            return {"checkout_url": existing.url}

    service = db.get(Service, booking.service_id)
    customer = db.get(Customer, booking.customer_id)
    session = payments.create_deposit_checkout(
        booking.id, service.name, booking.deposit_cents, customer.email
    )
    booking.stripe_checkout_session_id = session.id
    db.commit()
    return {"checkout_url": session.url}


@app.get("/bookings/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Look up one booking (handy for checking its status)."""
    booking = db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Stripe calls this when something happens to a payment."""
    # 1. Prove it's really Stripe (anyone could call this URL).
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = payments.verify_webhook(payload, signature)
    except (ValueError, stripe.SignatureVerificationError) as error:
        logger.warning("Stripe webhook rejected: %s", error)
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Idempotency: Stripe may send the same event twice. Only act once.
    db.add(StripeEvent(id=event.id, type=event.type))
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        return {"received": True, "duplicate": True}

    # 3. Which booking is this about? (we put booking_id in metadata in Phase 5)
    session = event.data.object.to_dict()  # plain Python dict, easier to read
    metadata = session.get("metadata") or {}
    booking = db.get(Booking, int(metadata["booking_id"])) if "booking_id" in metadata else None

    # 4. Update the booking.
    if booking is not None and booking.status == "pending":
        if event.type == "checkout.session.completed" and session.get("payment_status") == "paid":
            booking.status = "confirmed"
            booking.stripe_payment_intent_id = session.get("payment_intent")
        elif event.type == "checkout.session.expired":
            booking.status = "cancelled"  # never paid, so free up the slot

    db.commit()
    return {"received": True}


@app.post("/bookings/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: int, request: CancelRequest, db: Session = Depends(get_db)):
    """A client cancels their own booking. Deposits are non-refundable."""
    booking = db.get(Booking, booking_id)
    # Same error for "no such booking" and "wrong token", so nobody can guess ids.
    if booking is None or not booking.manage_token or not secrets.compare_digest(
        booking.manage_token, request.token
    ):
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in ACTIVE_STATUSES:
        raise HTTPException(status_code=409, detail="This booking can't be cancelled")

    # Unpaid? Close the payment page so it can't be paid after cancelling.
    if booking.status == "pending" and booking.stripe_checkout_session_id:
        payments.expire_checkout(booking.stripe_checkout_session_id)

    booking.status = "cancelled"
    db.commit()
    return booking


def require_admin(x_admin_key: str = Header(default="")):
    """Only you (with the admin key) can use admin endpoints."""
    if not settings.admin_api_key or not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(status_code=401, detail="Admin key required")


@app.post("/admin/bookings/{booking_id}/cancel", response_model=BookingOut, dependencies=[Depends(require_admin)])
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


@app.post("/admin/bookings/{booking_id}/no-show", response_model=BookingOut, dependencies=[Depends(require_admin)])
def mark_no_show(booking_id: int, db: Session = Depends(get_db)):
    """The client didn't turn up. You keep the deposit."""
    return set_final_status(db, booking_id, "no_show")


@app.post("/admin/bookings/{booking_id}/complete", response_model=BookingOut, dependencies=[Depends(require_admin)])
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
