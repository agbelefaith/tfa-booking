"""Put TFA's real menu on the site.

Run from the backend folder:  python load_menu.py
Safe to run again: it updates by name instead of making duplicates.
Anything not on the menu below gets hidden (is_active=False), not deleted,
so old bookings that point at it still work.
"""
from sqlalchemy import select

from app.db import SessionLocal
from app.models import AddOn, Service

# (name, minutes, price in cents). The 3 hours already includes cleanup.
SERVICES = [
    ("Short plain set", 180, 3500),
    ("Medium plain set", 180, 4000),
    ("Long plain set", 180, 4500),
    ("Short French set", 180, 4000),
    ("Medium French set", 180, 4500),
    ("Long French set", 180, 5000),
]

ADD_ONS = [
    ("Simple nail art", 5, 500),
    ("Minimal nail art", 10, 1000),
    ("Detailed nail art", 20, 1500),
    ("Extra detailed nail art", 25, 2000),
    ("Removal", 60, 1000),
]


def sync(db, model, rows, minutes_field):
    """Make the table match the menu: update or add these rows, hide the rest."""
    menu_names = {name for name, _, _ in rows}

    for name, minutes, price in rows:
        item = db.scalar(select(model).where(model.name == name))
        if item is None:
            item = model(name=name)
            db.add(item)
        setattr(item, minutes_field, minutes)
        item.price_cents = price
        item.is_active = True

    for item in db.scalars(select(model)):
        if item.name not in menu_names:
            item.is_active = False


def main():
    with SessionLocal() as db:
        sync(db, Service, SERVICES, "duration_minutes")
        for service in db.scalars(select(Service)):
            service.buffer_minutes = 0  # cleanup is inside the 3 hours
        sync(db, AddOn, ADD_ONS, "extra_minutes")
        db.commit()
        print("Menu loaded ✅")


if __name__ == "__main__":
    main()
