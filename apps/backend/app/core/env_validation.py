"""Validate environment-specific settings at startup (fail fast in production)."""

from __future__ import annotations

import logging

from app.core.settings import Settings

logger = logging.getLogger(__name__)

# Values that must never be used in production
_FORBIDDEN_JWT_SECRETS = frozenset(
    {
        "",
        "change_me_in_real_env",
        "changeme",
        "secret",
        "test",
        "password",
    }
)

_MIN_JWT_SECRET_LEN = 32


def _is_production_like(env: str) -> bool:
    return env.strip().lower() in {"production", "staging", "prod"}


def validate_settings_for_environment(settings: Settings) -> None:
    """
    Raise ValueError if critical security settings are unsafe for the current environment.
    """
    cors = [o.strip() for o in (settings.CORS_ORIGINS or "").split(",") if o.strip()]
    if not settings.is_local_environment and not cors:
        msg = "CORS_ORIGINS must list at least one browser origin (comma-separated)."
        raise ValueError(msg)

    env = settings.ENVIRONMENT
    if not _is_production_like(env):
        return

    secret = (settings.JWT_SECRET or "").strip()
    if secret.lower() in {x.lower() for x in _FORBIDDEN_JWT_SECRETS} or secret in _FORBIDDEN_JWT_SECRETS:
        msg = "JWT_SECRET must be set to a strong, unique value in production (not a placeholder)."
        raise ValueError(msg)
    if len(secret) < _MIN_JWT_SECRET_LEN:
        msg = f"JWT_SECRET must be at least {_MIN_JWT_SECRET_LEN} characters in production."
        raise ValueError(msg)

    if not cors:
        msg = "CORS_ORIGINS must list explicit browser origins in production (comma-separated)."
        raise ValueError(msg)
    if any(o == "*" for o in cors):
        msg = "CORS_ORIGINS must not use '*' in production; list explicit origins."
        raise ValueError(msg)


def log_production_warnings(settings: Settings) -> None:
    """Non-fatal hints for production deployments."""
    if not _is_production_like(settings.ENVIRONMENT):
        return
    if not (settings.TRUSTED_HOSTS or "").strip():
        logger.warning(
            "TRUSTED_HOSTS is unset. Consider setting it (comma-separated hostnames) "
            "and enabling trusted-host middleware for stricter request Host validation."
        )
