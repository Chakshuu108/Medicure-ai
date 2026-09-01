"""Async background scheduler for proactive Health Guardian scans."""

from __future__ import annotations

import asyncio
import logging

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.services.proactive_monitor_service import run_proactive_scan_all

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None


async def _scan_loop() -> None:
    settings = get_settings()
    assert _stop_event is not None

    if settings.guardian_startup_delay_seconds > 0:
        logger.info(
            "Proactive Health Guardian: first scan in %ss",
            settings.guardian_startup_delay_seconds,
        )
        try:
            await asyncio.wait_for(
                _stop_event.wait(),
                timeout=settings.guardian_startup_delay_seconds,
            )
            return
        except asyncio.TimeoutError:
            pass

    interval_seconds = max(3600.0, settings.guardian_scan_interval_hours * 3600)

    while not _stop_event.is_set():
        if settings.guardian_proactive_enabled:
            try:
                async with AsyncSessionLocal() as db:
                    await run_proactive_scan_all(db)
                    await db.commit()
            except Exception:
                logger.exception("Proactive Health Guardian scan failed")
        else:
            logger.debug("Proactive Health Guardian disabled — skipping scan")

        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=interval_seconds)
            break
        except asyncio.TimeoutError:
            continue


def start_proactive_scheduler() -> None:
    global _task, _stop_event
    settings = get_settings()
    if not settings.guardian_proactive_enabled:
        logger.info("Proactive Health Guardian scheduler is disabled")
        return
    if _task and not _task.done():
        return

    _stop_event = asyncio.Event()
    _task = asyncio.create_task(_scan_loop(), name="proactive-guardian-scheduler")
    logger.info(
        "Proactive Health Guardian scheduler started (every %sh)",
        settings.guardian_scan_interval_hours,
    )


async def stop_proactive_scheduler() -> None:
    global _task, _stop_event
    if _stop_event:
        _stop_event.set()
    if _task:
        try:
            await asyncio.wait_for(_task, timeout=10)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            _task.cancel()
        _task = None
    _stop_event = None
