"""Tests for the dedicated reminder scheduler CLI.

Idempotency and duplicate-send prevention are implemented in ``run_due_reminders`` and
``EventReminderRun``; see ``tests/test_event_reminders.py``.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.cli.reminder_scheduler import run_reminder_scheduler_tick
from app.modules.event_reminders.schemas import RunDueRemindersResponse


@pytest.mark.asyncio
async def test_run_reminder_scheduler_tick_delegates_to_service() -> None:
    fake = RunDueRemindersResponse(
        rules_considered=2,
        reminders_sent=1,
        skipped_not_due=0,
        skipped_already_sent=0,
        skipped_invalid=0,
        failed=0,
        failure_messages=[],
    )

    @asynccontextmanager
    async def null_session():
        yield MagicMock()

    def fake_factory() -> object:
        return null_session()

    with (
        patch("app.cli.reminder_scheduler.async_session_factory", fake_factory),
        patch(
            "app.cli.reminder_scheduler.event_reminders_service.run_due_reminders",
            new_callable=AsyncMock,
            return_value=fake,
        ) as mock_run,
    ):
        out = await run_reminder_scheduler_tick()
    assert out is fake
    mock_run.assert_awaited_once()
