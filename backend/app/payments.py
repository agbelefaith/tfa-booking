"""Everything that talks to Stripe lives here."""
import time

import stripe

from app.config import settings

stripe.api_key = settings.stripe_secret_key

CHECKOUT_EXPIRES_AFTER_MINUTES = 31  # Stripe needs at least 30; 1 extra for clock delays


def create_deposit_checkout(booking_id: int, service_name: str, deposit_cents: int, email: str):
    """Ask Stripe for a hosted payment page for this booking's deposit."""
    return stripe.checkout.Session.create(
        mode="payment",
        customer_email=email,
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": "eur",
                    "unit_amount": deposit_cents,
                    "product_data": {"name": f"Deposit: {service_name}"},
                },
            }
        ],
        metadata={"booking_id": str(booking_id)},
        expires_at=int(time.time()) + CHECKOUT_EXPIRES_AFTER_MINUTES * 60,
        success_url=f"{settings.frontend_url}/booking/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.frontend_url}/booking/cancelled?booking_id={booking_id}",
    )


def get_checkout(session_id: str):
    """Look up a payment page Stripe already made."""
    return stripe.checkout.Session.retrieve(session_id)


def verify_webhook(payload: bytes, signature: str):
    """Check a webhook really came from Stripe, then turn it into an event."""
    return stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)


def expire_checkout(session_id: str):
    """Close a payment page so it can't be paid any more."""
    return stripe.checkout.Session.expire(session_id)


def refund_deposit(booking_id: int, payment_intent_id: str):
    """Give a client their deposit back.

    The idempotency key means that if this runs twice (a retry, a double
    click), Stripe still only refunds once.
    """
    return stripe.Refund.create(
        payment_intent=payment_intent_id,
        idempotency_key=f"refund-booking-{booking_id}",
    )
