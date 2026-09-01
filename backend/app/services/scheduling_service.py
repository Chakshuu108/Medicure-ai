"""Google OAuth, calendar sync, and medication schedule preview."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models import Medicine, Patient, Prescription

CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URI = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPES = "openid email profile https://www.googleapis.com/auth/calendar.events"

FREQUENCY_LABELS = {
    "once": "Once only",
    "daily": "Every day",
    "alternate_days": "Alternate days",
    "every_3_days": "Every 3 days",
    "weekly": "Once a week",
    "as_needed": "As needed (PRN)",
}


def frequency_label(pattern: str) -> str:
    return FREQUENCY_LABELS.get(pattern or "daily", (pattern or "daily").replace("_", " "))


def _parse_dose_times(medicine: Medicine) -> list[str]:
    raw = (getattr(medicine, "dose_times", None) or "").strip()
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and parsed:
                return [str(t)[:5] for t in parsed]
        except json.JSONDecodeError:
            pass
    start_time = (getattr(medicine, "start_time", None) or "").strip() or "08:00"
    times_per_day = int(getattr(medicine, "times_per_day", None) or 1)
    return _compute_dose_times(start_time, times_per_day)


DOSE_OFFSET_HOURS = {
    1: [0],
    2: [0, 12],
    3: [0, 6, 12],
    4: [0, 6, 12, 18],
    5: [0, 5, 10, 15, 20],
    6: [0, 4, 8, 12, 16, 20],
}


def compute_dose_times(start_time: str, times_per_day: int) -> list[str]:
    return _compute_dose_times(start_time, times_per_day)


def _compute_dose_times(start_time: str, times_per_day: int) -> list[str]:
    try:
        hour, minute = map(int, start_time.split(":")[:2])
    except (ValueError, TypeError):
        hour, minute = 8, 0
    if times_per_day <= 1:
        return [f"{hour:02d}:{minute:02d}"]
    offsets = DOSE_OFFSET_HOURS.get(times_per_day) or [
        i * (20 / max(times_per_day - 1, 1)) for i in range(times_per_day)
    ]
    times: list[str] = []
    for offset in offsets:
        total_minutes = hour * 60 + minute + int(round(offset * 60))
        capped = min(total_minutes, 22 * 60)
        times.append(f"{capped // 60:02d}:{capped % 60:02d}")
    return times


def _iter_schedule_offsets(duration_days: int, pattern: str) -> list[int]:
    duration = max(1, int(duration_days or 7))
    pattern = (pattern or "daily").lower()
    if pattern == "once":
        return [0]
    if pattern == "as_needed":
        return []
    offsets: list[int] = []
    for offset in range(duration):
        if pattern == "daily":
            offsets.append(offset)
        elif pattern == "alternate_days" and offset % 2 == 0:
            offsets.append(offset)
        elif pattern == "every_3_days" and offset % 3 == 0:
            offsets.append(offset)
        elif pattern == "weekly" and offset % 7 == 0:
            offsets.append(offset)
    return offsets


def _medicine_start_date(medicine: Medicine) -> date | None:
    raw = (getattr(medicine, "start_date", None) or "").strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def medicine_to_dict(medicine: Medicine) -> dict:
    pattern = getattr(medicine, "frequency_pattern", None) or "daily"
    times_per_day = int(getattr(medicine, "times_per_day", None) or 1)
    dose_times = _parse_dose_times(medicine)
    return {
        "id": medicine.id,
        "name": medicine.name,
        "disease": getattr(medicine, "disease", "") or "",
        "dosage": medicine.dosage,
        "duration_days": medicine.duration_days,
        "timing": medicine.timing,
        "frequency_pattern": pattern,
        "frequency_label": frequency_label(pattern),
        "times_per_day": times_per_day,
        "dose_times": dose_times,
        "start_date": getattr(medicine, "start_date", "") or "",
        "start_time": getattr(medicine, "start_time", "") or "",
        "schedule_ready": bool((getattr(medicine, "start_date", "") or "").strip()),
    }


def _build_med_events(medicine: Medicine, patient_name: str) -> list[dict]:
    pattern = getattr(medicine, "frequency_pattern", None) or "daily"
    if pattern == "as_needed":
        return []

    start = _medicine_start_date(medicine)
    if not start:
        return []

    duration = int(getattr(medicine, "duration_days", None) or 7)
    dose_times = _parse_dose_times(medicine)
    offsets = _iter_schedule_offsets(duration, pattern)
    events: list[dict] = []

    for day_offset in offsets:
        current_date = start + timedelta(days=day_offset)
        for t in dose_times:
            hour, minute = map(int, t.split(":"))
            start_dt = datetime(current_date.year, current_date.month, current_date.day, hour, minute)
            end_dt = start_dt + timedelta(minutes=15)
            events.append({
                "summary": f"Medicine: {medicine.name} {medicine.dosage}",
                "description": (
                    f"Medication for {patient_name}\n"
                    f"Pattern: {frequency_label(pattern)}\n"
                    f"Dose times: {', '.join(dose_times)}"
                ),
                "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 10}]},
            })
    return events


def _build_schedule_rows(medicine: Medicine) -> list[dict]:
    pattern = getattr(medicine, "frequency_pattern", None) or "daily"
    if pattern == "as_needed":
        return []

    start = _medicine_start_date(medicine)
    if not start:
        return []

    duration = int(getattr(medicine, "duration_days", None) or 7)
    dose_times = _parse_dose_times(medicine)
    offsets = _iter_schedule_offsets(duration, pattern)
    rows: list[dict] = []

    for day_offset in offsets:
        current_date = start + timedelta(days=day_offset)
        date_str = current_date.isoformat()
        for t in dose_times:
            rows.append({
                "date": date_str,
                "time": t,
                "medicine": medicine.name,
                "dosage": medicine.dosage,
                "timing": frequency_label(pattern),
                "frequency_pattern": pattern,
                "medicine_id": medicine.id,
            })
    return rows


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


async def get_schedule_preview(db: AsyncSession, patient_id: str) -> list[dict]:
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.medicines))
        .where(Prescription.patient_id == patient_id)
        .order_by(Prescription.created_at.desc())
    )
    prescriptions = result.scalars().all()
    if not prescriptions:
        return []

    schedule: list[dict] = []
    for prescription in prescriptions:
        for medicine in prescription.medicines:
            schedule.extend(_build_schedule_rows(medicine))

    schedule.sort(key=lambda x: (x["date"], x["time"], x["medicine"]))
    return schedule[:120]


async def sync_to_google_calendar(db: AsyncSession, patient_id: str, access_token: str) -> dict:
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.medicines))
        .where(Prescription.patient_id == patient_id)
        .order_by(Prescription.created_at.desc())
    )
    prescriptions = result.scalars().all()
    if not prescriptions:
        return {"success": False, "message": "No prescriptions found", "events_created": 0}

    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    patient_name = patient.name if patient else "Patient"

    all_events: list[dict] = []
    for prescription in prescriptions:
        for medicine in prescription.medicines:
            all_events.extend(_build_med_events(medicine, patient_name)[:30])

    if not all_events:
        return {
            "success": False,
            "message": "Set a start date & time for each medicine before syncing to calendar.",
            "events_created": 0,
        }

    created = 0
    errors: list[str] = []
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30) as client:
        for event in all_events[:40]:
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
