"""Entry point for the FastAPI backend."""
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AddOn, Service
from app.schemas import AddOnOut, ServiceOut

from app.config import settings
from app.db import get_db

app = FastAPI(title=settings.app_name)


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
