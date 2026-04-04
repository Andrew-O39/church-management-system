"""
Dedicated process: periodically runs the same due-reminder job as POST /notifications/jobs/run-reminders.

Run locally:
  poetry run reminder-scheduler

Docker Compose includes a `reminder_scheduler` service using this entrypoint.
"""

from __future__ import annotations

import asyncio
import logging

from app.core.logging import configure_logging
from app.core.settings import settings
from app.db.session import async_session_factory
from app.modules.event_reminders import service as event_reminders_service
from app.modules.event_reminders.schemas import RunDueRemindersResponse

logger = logging.getLogger(__name__)


async def run_reminder_scheduler_tick() -> RunDueRemindersResponse:
    """One job execution — same DB work as the admin HTTP trigger."""
    async with async_session_factory() as session:
        return await event_reminders_service.run_due_reminders(session)


async def run_forever() -> None:
    interval = max(1, settings.REMINDER_JOB_INTERVAL_SECONDS)
    logger.info(
        "reminder_scheduler_started interval_seconds=%s batch_size=%s",
        interval,
        settings.REMINDER_JOB_BATCH_SIZE,
    )
    while True:
        try:
            result = await run_reminder_scheduler_tick()
            logger.info(
                "reminder_job_tick sent=%s considered=%s skipped_not_due=%s "
                "skipped_already_sent=%s skipped_invalid=%s failed=%s",
                result.reminders_sent,
                result.rules_considered,
                result.skipped_not_due,
                result.skipped_already_sent,
                result.skipped_invalid,
                result.failed,
            )
            if result.failure_messages:
                for msg in result.failure_messages[:15]:
                    logger.warning("reminder_job_failure_detail %s", msg)
        except Exception:
            logger.exception("reminder_job_tick_failed")
        await asyncio.sleep(interval)


async def _run_disabled_hold() -> None:
    """Keep the container alive without polling DB when scheduling is turned off (avoids Docker restart thrash)."""
    logger.info(
        "reminder_scheduler_disabled REMINDER_SCHEDULER_ENABLED=false; idle (no DB polling). "
        "Remove the service or set REMINDER_SCHEDULER_ENABLED=true to enable ticks.",
    )
    await asyncio.Event().wait()


def main() -> None:
    configure_logging()
    try:
        if not settings.REMINDER_SCHEDULER_ENABLED:
            asyncio.run(_run_disabled_hold())
        else:
            asyncio.run(run_forever())
    except KeyboardInterrupt:
        logger.info("reminder_scheduler_stopped keyboard_interrupt")


if __name__ == "__main__":
    main()
