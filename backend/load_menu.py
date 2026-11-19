"""Put TFA's real menu on the site.

Run from the backend folder:  python load_menu.py
Safe to run again: it updates by name instead of making duplicates.
Anything not on the menu below gets hidden (is_active=False), not deleted,
so old bookings that point at it still work.
"""
from sqlalchemy import select

from app.db import SessionLocal
from app.models import AddOn, Service

# (name, minutes, price in cents, allows nail art). The 3 hours already includes cleanup.
SERVICES = [
    ("Short plain set", 180, 3500, False),
    ("Medium plain set", 180, 4000, False),
    ("Long plain set", 180, 4500, False),
    ("Short French set", 180, 4000, True),
    ("Medium French set", 180, 4500, True),
    ("Long French set", 180, 5000, True),
]
SERVICE_FIELDS = ("name", "duration_minutes", "price_cents", "allows_nail_art")

# (name, extra minutes, price in cents, is nail art)
ADD_ONS = [
    ("Simple nail art", 5, 500, True),
    ("Minimal nail art", 10, 1000, True),
    ("Detailed nail art", 20, 1500, True),
    ("Extra detailed nail art", 25, 2000, True),
    ("Removal", 60, 1000, False),
]
ADD_ON_FIELDS = ("name", "extra_minutes", "price_cents", "is_nail_art")


def sync(db, model, rows, fields):
    """Make the table match the menu: update or add these rows, hide the rest."""
    menu_names = {row[0] for row in rows}

    for row in rows:
        values = dict(zip(fields, row))
        item = db.scalar(select(model).where(model.name == values["name"]))
        if item is None:
            item = model(name=values["name"])
            db.add(item)
        for field, value in values.items():
            setattr(item, field, value)
        item.is_active = True

    for item in db.scalars(select(model)):
        if item.name not in menu_names:
            item.is_active = False


def main():
    with SessionLocal() as db:
        sync(db, Service, SERVICES, SERVICE_FIELDS)
        for service in db.scalars(select(Service)):
            service.buffer_minutes = 0  # cleanup is inside the 3 hours
        sync(db, AddOn, ADD_ONS, ADD_ON_FIELDS)
        db.commit()
        print("Menu loaded ✅")


if __name__ == "__main__":
    main()
