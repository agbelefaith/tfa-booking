"""Database connection setup.

engine  = the connection to Postgres (made once, shared by the whole app)
session = one "conversation" with the database (opened per request, then closed)
Base    = every table class inherits from this
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Tell SQLAlchemy to use the psycopg (v3) driver to talk to Postgres.
database_url = settings.database_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(database_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Parent class for all our tables."""


def get_db():
    """Give an endpoint a session, and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
