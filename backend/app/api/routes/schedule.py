from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import require_roles
from app.database import get_db
from app.models import Medicine, Prescription
from app.schemas.api import MedicineScheduleUpdate
from app.services.scheduling_service import (
    compute_dose_times,
    exchange_google_code,
    get_google_auth_url,
    get_patient_google_access_token,
    get_schedule_preview,
    medicine_to_dict,
    refresh_google_token,
    sync_to_google_calendar,
)

router = APIRouter(prefix="/api", tags=["schedule"])


class GoogleCodeRequest(BaseModel):
    code: str


class GoogleRefreshRequest(BaseModel):
    refresh_token: str


class CalendarSyncRequest(BaseModel):
    access_token: str | None = None


@router.get("/auth/google/url")
async def google_auth_url(purpose: str = Query("patient_login")):
    try:
        return {"url": get_google_auth_url(state=purpose)}
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/auth/google/callback")
async def google_auth_callback(data: GoogleCodeRequest):
    try:
        tokens = await exchange_google_code(data.code)
        return {
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
            "expires_in": tokens.get("expires_in"),
        }
    except Exception as exc:
        raise HTTPException(400, f"Google OAuth failed: {exc}") from exc


@router.post("/auth/google/refresh")
async def google_refresh_token(data: GoogleRefreshRequest):
    try:
        tokens = await refresh_google_token(data.refresh_token)
        return {"access_token": tokens.get("access_token"), "expires_in": tokens.get("expires_in")}
    except Exception as exc:
        raise HTTPException(400, f"Token refresh failed: {exc}") from exc


@router.get("/patient/schedule/preview")
async def schedule_preview(
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    items = await get_schedule_preview(db, current["user_id"])
    return {"schedule": items}


@router.patch("/patient/medicines/{medicine_id}/schedule")
async def update_medicine_schedule(
    medicine_id: str,
    data: MedicineScheduleUpdate,
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    import json

    result = await db.execute(
        select(Medicine)
        .join(Prescription, Medicine.prescription_id == Prescription.id)
        .where(Medicine.id == medicine_id, Prescription.patient_id == current["user_id"])
    )
    medicine = result.scalar_one_or_none()
    if not medicine:
        raise HTTPException(404, "Medicine not found")

    dose_times = data.dose_times or compute_dose_times(data.start_time, int(medicine.times_per_day or 1))
    medicine.start_date = data.start_date[:10]
    medicine.start_time = data.start_time[:5]
    medicine.dose_times = json.dumps(dose_times)
    await db.flush()
    return {"medicine": medicine_to_dict(medicine)}


@router.post("/patient/schedule/sync-calendar")
async def sync_calendar(
    data: CalendarSyncRequest | None = None,
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    patient = current["user"]
    token = (data.access_token if data else None) or None
    if not token:
        token = await get_patient_google_access_token(patient)
    if not token:
        raise HTTPException(
            400,
            "Google Calendar not linked. Sign out and sign in again with Google.",
        )
    return await sync_to_google_calendar(db, current["user_id"], token)
