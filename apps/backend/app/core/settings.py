from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---- Runtime ----
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "info"

    # ---- Database ----
    # Supports asyncpg URL format for SQLAlchemy async usage.
    DATABASE_URL: str = "postgresql+asyncpg://church_user:church_password@localhost:5432/church_mvp"

    # Comma-separated list of allowed CORS origins.
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Base prefix for API routes (domain routers).
    API_PREFIX: str = "/api/v1"

    # ---- Auth placeholders (JWT-based, not implemented in Step 1) ----
    JWT_SECRET: str = "change_me_in_real_env"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ---- Multi-tenant readiness (single tenant by default) ----
    TENANCY_MODE: str = "single_tenant"  # later: "schema_per_tenant" / "db_per_tenant" etc.
    TENANT_ID: str = "default"

    # ---- Dev bootstrap (optional; see README / `poetry run bootstrap-admin`) ----
    BOOTSTRAP_ADMIN_EMAIL: str | None = None
    BOOTSTRAP_ADMIN_PASSWORD: str | None = None

    # ---- SMS (Twilio-compatible HTTP API; optional in local dev) ----
    SMS_PROVIDER: str | None = None  # e.g. "twilio"; unset = SMS sends fail with clear message
    SMS_ACCOUNT_SID: str | None = None
    SMS_AUTH_TOKEN: str | None = None
    SMS_FROM_NUMBER: str | None = None

    # ---- WhatsApp (Twilio WhatsApp API; optional; uses profile phone as E.164) ----
    WHATSAPP_PROVIDER: str | None = None  # e.g. "twilio"
    WHATSAPP_ACCOUNT_SID: str | None = None  # defaults to SMS_ACCOUNT_SID when unset
    WHATSAPP_AUTH_TOKEN: str | None = None  # defaults to SMS_AUTH_TOKEN when unset
    # E.g. whatsapp:+14155238886 (Twilio sandbox / approved sender)
    WHATSAPP_FROM_NUMBER: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Convenient singleton used across the app.
settings = get_settings()

