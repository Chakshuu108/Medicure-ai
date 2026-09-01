from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import require_roles
from app.database import get_db
from app.models import Patient
from app.services.scheduling_service import (
    exchange_google_code,
    get_google_auth_url,
    get_patient_google_access_token,
    get_schedule_preview,
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
