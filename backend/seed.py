"""Add sample data so the booking page has something to show.

Run from the backend folder:  python seed.py
Swap these for your real TFA services and prices any time.
"""
from datetime import time

from sqlalchemy import select

from app.db import SessionLocal
from app.models import AddOn, Service, WeeklyHours


def main():
    with SessionLocal() as db:
        if db.scalar(select(Service).limit(1)):
            print("Already has data, skipping.")
            return

        db.add_all([
            Service(name="Gel manicure", duration_minutes=60, buffer_minutes=10,
                    price_cents=3500),
            Service(name="BIAB", duration_minutes=75, buffer_minutes=10,
                    price_cents=4500),
            Service(name="Acrylic full set", duration_minutes=90, buffer_minutes=15,
                    price_cents=5000),
            AddOn(name="Nail art", extra_minutes=15, price_cents=1000),
            AddOn(name="Chrome", extra_minutes=10, price_cents=500),
            AddOn(name="Removal", extra_minutes=20, price_cents=1000),
            WeeklyHours(day_of_week=5, opens_at=time(10, 0), closes_at=time(18, 0)),
        ])
        db.commit()
        print("Sample data added ✅")


if __name__ == "__main__":
    main()
