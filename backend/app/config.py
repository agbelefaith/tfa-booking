"""App settings, loaded from environment variables (or a local .env file).

Keeping config here means secrets never live in the code itself.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TFA Booking"
    environment: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/tfa_booking"
    business_timezone: str = "Europe/Dublin"
    public_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"
    admin_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = Settings()
