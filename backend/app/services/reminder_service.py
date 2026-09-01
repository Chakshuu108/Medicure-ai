"""Missed MCQ detection — email + Google Calendar reminders (no doctor alerts)."""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentMemory, MCQResponse, Patient
from app.services.email_service import send_missed_checkin_email
from app.services.scheduling_service import create_mcq_reminder_event


async def _reminder_already_sent(db: AsyncSession, patient_id: str, missed_date: str) -> bool:
    result = await db.execute(
        select(AgentMemory).where(
            AgentMemory.patient_id == patient_id,
            AgentMemory.memory_type == "mcq_reminder_sent",
            AgentMemory.content == missed_date,
        )
    )
    return result.scalars().first() is not None


async def _mark_reminder_sent(db: AsyncSession, patient_id: str, missed_date: str) -> None:
    db.add(AgentMemory(
        patient_id=patient_id,
        memory_type="mcq_reminder_sent",
        content=missed_date,
        metadata_json={"sent_at": datetime.now().isoformat()},
    ))


async def process_missed_mcq_reminders(
    db: AsyncSession,
    patient: Patient,
    google_access_token: str | None = None,
    lookback_days: int = 14,
) -> dict:
    today = date.today()
    start = today - timedelta(days=lookback_days - 1)

    result = await db.execute(
        select(MCQResponse.date)
        .where(MCQResponse.patient_id == patient.id, MCQResponse.date >= start.isoformat())
    )
    completed_dates = {r[0] for r in result.all()}

    emails_sent = 0
    calendar_events = 0
    missed_dates: list[str] = []
    errors: list[str] = []

    current = start
    while current < today:
        ds = current.isoformat()
        if ds not in completed_dates:
            missed_dates.append(ds)
            if not await _reminder_already_sent(db, patient_id=patient.id, missed_date=ds):
                if patient.email:
                    ok, msg = await send_missed_checkin_email(patient.name, patient.email, ds)
                    if ok:
                        emails_sent += 1
                    else:
                        errors.append(f"Email {ds}: {msg}")

                if google_access_token:
                    ok, msg = await create_mcq_reminder_event(
                        google_access_token, patient.name, ds,
                    )
                    if ok:
                        calendar_events += 1
                    elif msg:
                        errors.append(f"Calendar {ds}: {msg}")

                await _mark_reminder_sent(db, patient.id, ds)
        current += timedelta(days=1)

    today_str = today.isoformat()
    if today_str not in completed_dates:
        missed_dates.append(today_str)
        hour = datetime.now().hour
        if hour >= 10 and not await _reminder_already_sent(db, patient.id, today_str):
            if patient.email:
                ok, _ = await send_missed_checkin_email(patient.name, patient.email, today_str)
                if ok:
                    emails_sent += 1
            if google_access_token:
                ok, _ = await create_mcq_reminder_event(google_access_token, patient.name, today_str)
                if ok:
                    calendar_events += 1
            await _mark_reminder_sent(db, patient.id, today_str)

    await db.flush()
    return {
        "missed_dates": missed_dates,
        "emails_sent": emails_sent,
        "calendar_events": calendar_events,
        "errors": errors[:5],
    }
