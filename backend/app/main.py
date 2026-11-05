"""Entry point for the FastAPI backend."""
from fastapi import FastAPI

from app.config import settings

app = FastAPI(title=settings.app_name)


@app.get("/health")
def health_check() -> dict:
    """Simple endpoint to confirm the API is running."""
    return {"status": "ok", "environment": settings.environment}
