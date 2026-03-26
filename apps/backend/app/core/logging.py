import logging

from app.core.settings import settings


def configure_logging() -> None:
    level_str = (settings.LOG_LEVEL or "info").upper()
    level = getattr(logging, level_str, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(levelname)s [%(name)s] %(message)s",
    )

