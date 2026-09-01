"""Google OAuth, calendar sync, and medication schedule preview."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models import Patient, Prescription

CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPES = "openid email profile https://www.googleapis.com/auth/calendar.events"

TIMING_MAP = {
    "morning": "08:00",
    "afternoon": "14:00",
    "evening": "18:00",
    "night": "21:00",
    "before bed": "22:00",
    "twice daily": "08:00",
    "thrice daily": "08:00",
}


def get_google_auth_url(state: str = "patient_login") -> str:
    settings = get_settings()
    if not settings.google_client_id:
        raise ValueError("Google OAuth not configured in backend/.env")
    params = urlencode({
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    })
    return f"{GOOGLE_AUTH_URI}?{params}"


async def exchange_google_code(code: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GOOGLE_TOKEN_URI, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        })
        resp.raise_for_status()
        return resp.json()


async def refresh_google_token(refresh_token: str) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(GOOGLE_TOKEN_URI, data={
            "refresh_token": refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        return resp.json()


async def get_google_user_info(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            GOOGLE_USERINFO_URI,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_patient_google_access_token(patient: Patient) -> str | None:
    if not patient.google_refresh_token:
        return None
    try:
        tokens = await refresh_google_token(patient.google_refresh_token)
        return tokens.get("access_token")
    except Exception:
        return None


def _parse_timing(timing_str: str) -> list[str]:
    timing_lower = (timing_str or "morning").lower()
    if "twice" in timing_lower:
        return ["08:00", "20:00"]
    if "thrice" in timing_lower or "3 times" in timing_lower:
        return ["08:00", "14:00", "20:00"]
    for key, val in TIMING_MAP.items():
        if key in timing_lower:
            return [val]
    return ["08:00"]


def _build_med_events(medicine, patient_name: str) -> list[dict]:
    start_date = date.today()
    duration = int(getattr(medicine, "duration_days", None) or 7)
    dose_times = _parse_timing(getattr(medicine, "timing", "morning"))
    events = []
    for day_offset in range(min(duration, 14)):
        current_date = start_date + timedelta(days=day_offset)
        for t in dose_times:
            hour, minute = map(int, t.split(":"))
            start_dt = datetime(current_date.year, current_date.month, current_date.day, hour, minute)
            end_dt = start_dt + timedelta(minutes=15)
            events.append({
                "summary": f"Medicine: {medicine.name} {medicine.dosage}",
                "description": f"Medication for {patient_name}\nTiming: {medicine.timing}",
                "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 10}]},
            })
    return events


async def get_schedule_preview(db: AsyncSession, patient_id: str) -> list[dict]:
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.medicines))
        .where(Prescription.patient_id == patient_id)
        .order_by(Prescription.created_at.desc())
        .limit(1)
    )
    prescription = result.scalar_one_or_none()
    if not prescription:
        return []

    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    patient_name = patient.name if patient else "Patient"

    schedule = []
    for medicine in prescription.medicines:
        for event in _build_med_events(medicine, patient_name)[:14]:
            schedule.append({
                "date": event["start"]["dateTime"][:10],
                "time": event["start"]["dateTime"][11:16],
                "medicine": medicine.name,
                "dosage": medicine.dosage,
                "timing": medicine.timing,
            })
    schedule.sort(key=lambda x: (x["date"], x["time"]))
    return schedule


async def sync_to_google_calendar(db: AsyncSession, patient_id: str, access_token: str) -> dict:
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.medicines))
        .where(Prescription.patient_id == patient_id)
        .order_by(Prescription.created_at.desc())
        .limit(1)
    )
    prescription = result.scalar_one_or_none()
    if not prescription or not prescription.medicines:
        return {"success": False, "message": "No prescriptions found", "events_created": 0}

    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    patient_name = patient.name if patient else "Patient"

    all_events: list[dict] = []
    for medicine in prescription.medicines:
        all_events.extend(_build_med_events(medicine, patient_name)[:7])

    created = 0
    errors: list[str] = []
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        for event in all_events:
            try:
                resp = await client.post(
                    f"{CALENDAR_BASE}/calendars/primary/events",
                    json=event,
                    headers=headers,
                )
                if resp.status_code in (200, 201):
                    created += 1
                else:
                    errors.append(resp.text[:120])
            except Exception as exc:
                errors.append(str(exc))

    if created:
        return {
            "success": True,
            "message": f"{created} medication reminder(s) added to Google Calendar.",
            "events_created": created,
        }
    return {
        "success": False,
        "message": "Failed to create calendar events.",
        "events_created": 0,
        "errors": errors[:3],
    }


async def create_mcq_reminder_event(
    access_token: str,
    patient_name: str,
    missed_date: str,
) -> tuple[bool, str]:
    try:
        start_dt = datetime.strptime(missed_date, "%Y-%m-%d").replace(hour=9, minute=0)
        end_dt = start_dt + timedelta(minutes=15)
        event = {
            "summary": "MediCure — Daily health check-in",
            "description": f"Reminder for {patient_name} to complete today's health check-in.",
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{CALENDAR_BASE}/calendars/primary/events",
                json=event,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code in (200, 201):
                return True, ""
            return False, resp.text[:120]
    except Exception as exc:
        return False, str(exc)
