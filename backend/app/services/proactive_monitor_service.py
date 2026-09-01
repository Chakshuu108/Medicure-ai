"""Background proactive monitoring — runs without patient login."""

from __future__ import annotations

import logging
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models import AgentMemory, AgentRun, Patient
from app.services.alert_service import create_clinical_alert
from app.services.email_service import send_proactive_wellness_nudge
from app.services.guardian_service import _perceive, run_guardian
from app.services.reminder_service import process_missed_mcq_reminders
from app.services.scheduling_service import get_patient_google_access_token

logger = logging.getLogger(__name__)

PROACTIVE_WORKFLOW = "guardian_proactive"
SILENCE_MEMORY_TYPE = "proactive_silence_alert"


async def _silence_already_flagged_today(db: AsyncSession, patient_id: str) -> bool:
    today = date.today().isoformat()
    result = await db.execute(
        select(AgentMemory).where(
            AgentMemory.patient_id == patient_id,
            AgentMemory.memory_type == SILENCE_MEMORY_TYPE,
            AgentMemory.content == today,
        )
    )
    return result.scalar_one_or_none() is not None


async def _mark_silence_flagged(db: AsyncSession, patient_id: str) -> None:
    db.add(AgentMemory(
        patient_id=patient_id,
        memory_type=SILENCE_MEMORY_TYPE,
        content=date.today().isoformat(),
        metadata_json={"sent_at": datetime.now().isoformat()},
    ))


async def _handle_silence_alert(db: AsyncSession, patient: Patient, days_silent: int) -> bool:
    """Rule-based alert when patient has not checked in for N days — no login required."""
    if days_silent < get_settings().guardian_silence_alert_days:
        return False
    if await _silence_already_flagged_today(db, patient.id):
        return False

    severity = "high" if days_silent >= 5 else "medium"
    message = (
        f"Health Guardian proactive scan: {patient.name} has not completed a daily health "
        f"check-in for {days_silent} day(s). Last activity may indicate disengagement or "
        f"missed self-monitoring."
    )
    await create_clinical_alert(
        db,
        patient_id=patient.id,
        doctor_id=patient.doctor_id,
        alert_type="Health Guardian — Missed Check-ins",
        message=message,
        severity=severity,
    )

    email = (patient.email or patient.google_email or "").strip()
    if email:
        await send_proactive_wellness_nudge(patient.name, email, days_silent)

    await _mark_silence_flagged(db, patient.id)
    return True


async def run_proactive_patient_monitor(db: AsyncSession, patient: Patient) -> dict:
    """Proactive scan for one patient (offline-safe)."""
    stats = {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "reminders": {},
        "silence_alert": False,
        "guardian_ran": False,
        "guardian_cached": False,
        "error": None,
    }

    try:
        google_token = await get_patient_google_access_token(patient)
        stats["reminders"] = await process_missed_mcq_reminders(
            db, patient, google_access_token=google_token,
        )

        snapshot = await _perceive(db, patient)
        stats["silence_alert"] = await _handle_silence_alert(
            db, patient, snapshot.get("days_silent", 0),
        )

        guardian_result = await run_guardian(
            db, patient.id, force=False, workflow_type=PROACTIVE_WORKFLOW,
        )
        stats["guardian_ran"] = True
        stats["guardian_cached"] = bool(guardian_result.get("cached"))
        stats["guardian_alerts"] = guardian_result.get("actions", {}).get("alerts_sent", 0)
    except Exception as exc:
        logger.exception("Proactive monitor failed for patient %s", patient.id)
        stats["error"] = str(exc)

    return stats


async def run_proactive_scan_all(db: AsyncSession) -> dict:
    """Scan every patient in the system — intended for scheduled background execution."""
    settings = get_settings()
    started = datetime.now()

    result = await db.execute(
        select(Patient).options(selectinload(Patient.doctor)).order_by(Patient.name)
    )
    patients = list(result.scalars().all())

    patient_stats: list[dict] = []
    totals = {
        "patients_scanned": 0,
        "emails_sent": 0,
        "silence_alerts": 0,
        "guardian_alerts": 0,
        "errors": 0,
    }

    for patient in patients:
        row = await run_proactive_patient_monitor(db, patient)
        patient_stats.append(row)
        totals["patients_scanned"] += 1
        if row.get("error"):
            totals["errors"] += 1
        if row.get("silence_alert"):
            totals["silence_alerts"] += 1
        totals["emails_sent"] += row.get("reminders", {}).get("emails_sent", 0)
        totals["guardian_alerts"] += row.get("guardian_alerts", 0)

    payload = {
        "ran_at": started.isoformat(),
        "duration_seconds": round((datetime.now() - started).total_seconds(), 2),
        "enabled": settings.guardian_proactive_enabled,
        "totals": totals,
        "patients": patient_stats,
    }

    run = AgentRun(
        patient_id=None,
        workflow_type="proactive_scan_global",
        status="completed",
        events=[],
        result=payload,
        completed_at=datetime.now(),
    )
    db.add(run)
    await db.flush()

    logger.info(
        "Proactive scan complete: %s patients, %s silence alerts, %s guardian alerts",
        totals["patients_scanned"],
        totals["silence_alerts"],
        totals["guardian_alerts"],
    )
    return payload


async def get_last_proactive_scan(db: AsyncSession) -> dict | None:
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.workflow_type == "proactive_scan_global", AgentRun.status == "completed")
        .order_by(AgentRun.started_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if not run or not run.result:
        return None
    return {
        "ran_at": run.result.get("ran_at") or (run.started_at.isoformat() if run.started_at else ""),
        "totals": run.result.get("totals", {}),
        "duration_seconds": run.result.get("duration_seconds"),
    }
