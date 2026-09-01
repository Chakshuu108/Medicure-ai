import asyncio
import json
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.events import AgentEventEmitter
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_roles,
    verify_password,
)
from app.database import get_db
from app.models import (
    Alert,
    ChatMessage,
    Doctor,
    Hospital,
    MCQResponse,
    MCQSet,
    Medicine,
    MeetSummary,
    OPDBooking,
    OPDSlot,
    Patient,
    Prescription,
    Receptionist,
)
from app.schemas.api import (
    BookSlotRequest,
    ChatRequest,
    DemoCredentials,
    DoctorCreate,
    HospitalRegister,
    LoginRequest,
    MCQSubmit,
    MeetSummaryCreate,
    OPDSlotCreate,
    PatientCreate,
    PatientGoogleLoginRequest,
    PatientLoginRequest,
    PrescriptionCreate,
    ReceptionistCreate,
    TokenResponse,
)
from app.services.scheduling_service import exchange_google_code, get_google_user_info
from app.services.agent_service import AgentWorkflowService
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["auth"])
settings = get_settings()


@router.get("/demo-credentials", response_model=list[DemoCredentials])
async def get_demo_credentials():
    return [
        DemoCredentials(role="admin", email_or_code="admin@medicure.demo", password="demo123",
                        description="Demo hospital only — real hospitals should Register hospital first"),
        DemoCredentials(role="doctor", email_or_code="doctor@medicure.demo", password="demo123",
                        description="Doctor — prescriptions, OPD, alerts, AI assistant"),
        DemoCredentials(role="receptionist", email_or_code="reception@medicure.demo", password="demo123",
                        description="Reception — register patients"),
        DemoCredentials(role="patient", email_or_code="PAT-DEMO-0001", password=None,
                        description="Patient — sign in with Google, then enter Patient ID"),
    ]


@router.post("/auth/admin/register", response_model=TokenResponse)
async def register_admin(data: HospitalRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Hospital).where(Hospital.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")
    hospital = Hospital(
        hospital_code=f"HOSP-{uuid4().hex[:6].upper()}",
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        address=data.address,
        phone=data.phone,
        city=data.city,
        website=data.website,
        pincode=data.pincode,
    )
    db.add(hospital)
    await db.flush()
    token = create_access_token({"sub": hospital.id, "role": "admin"})
    return TokenResponse(
        access_token=token,
        role="admin",
        user_id=hospital.id,
        name=hospital.name,
        hospital_id=hospital.id,
        extra={"hospital_code": hospital.hospital_code, "email": hospital.email},
    )


@router.post("/auth/admin/login", response_model=TokenResponse)
async def login_admin(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Hospital).where(Hospital.email == data.email))
    hospital = result.scalar_one_or_none()
    if not hospital or not verify_password(data.password, hospital.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": hospital.id, "role": "admin"})
    return TokenResponse(
        access_token=token,
        role="admin",
        user_id=hospital.id,
        name=hospital.name,
        hospital_id=hospital.id,
        extra={"hospital_code": hospital.hospital_code, "email": hospital.email},
    )


@router.post("/auth/doctor/login", response_model=TokenResponse)
async def login_doctor(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Doctor).where(Doctor.email == data.email))
    doctor = result.scalar_one_or_none()
    if not doctor or not verify_password(data.password, doctor.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": doctor.id, "role": "doctor"})
    return TokenResponse(access_token=token, role="doctor", user_id=doctor.id, name=doctor.name,
                         hospital_id=doctor.hospital_id, extra={"specialization": doctor.specialization})


@router.post("/auth/receptionist/login", response_model=TokenResponse)
async def login_receptionist(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Receptionist).where(Receptionist.email == data.email))
    rec = result.scalar_one_or_none()
    if not rec or not verify_password(data.password, rec.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"sub": rec.id, "role": "receptionist"})
    return TokenResponse(access_token=token, role="receptionist", user_id=rec.id, name=rec.name,
                         hospital_id=rec.hospital_id)


@router.post("/auth/patient/login", response_model=TokenResponse)
async def login_patient(data: PatientLoginRequest, db: AsyncSession = Depends(get_db)):
    """Legacy code-only login — use /auth/patient/google-login in the app."""
    result = await db.execute(select(Patient).where(Patient.patient_code == data.patient_code))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(401, "Invalid patient code")
    token = create_access_token({"sub": patient.id, "role": "patient"})
    return TokenResponse(access_token=token, role="patient", user_id=patient.id, name=patient.name,
                         hospital_id=patient.hospital_id,
                         extra={"patient_code": patient.patient_code, "doctor_id": patient.doctor_id})


@router.post("/auth/patient/google-login", response_model=TokenResponse)
async def login_patient_google(data: PatientGoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    """Patient login: Google OAuth + patient ID verification. Calendar access included."""
    try:
        tokens = await exchange_google_code(data.code)
    except Exception as exc:
        raise HTTPException(400, f"Google sign-in failed: {exc}") from exc

    access_token = tokens.get("access_token")
    if not access_token:
        raise HTTPException(400, "Google did not return an access token.")

    try:
        profile = await get_google_user_info(access_token)
    except Exception as exc:
        raise HTTPException(400, f"Could not read Google profile: {exc}") from exc

    google_email = (profile.get("email") or "").strip()

    result = await db.execute(
        select(Patient).where(Patient.patient_code == data.patient_code.strip())
    )
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(401, "Invalid patient ID. Check the code from your hospital registration.")

    patient.google_email = google_email
    refresh = tokens.get("refresh_token")
    if refresh:
        patient.google_refresh_token = refresh
    if google_email and not patient.email:
        patient.email = google_email

    await db.flush()

    jwt = create_access_token({"sub": patient.id, "role": "patient"})
    return TokenResponse(
        access_token=jwt,
        role="patient",
        user_id=patient.id,
        name=patient.name,
        hospital_id=patient.hospital_id,
        extra={
            "patient_code": patient.patient_code,
            "doctor_id": patient.doctor_id,
            "google_email": google_email,
            "google_access_token": access_token,
            "google_refresh_token": refresh or patient.google_refresh_token,
            "calendar_connected": bool(patient.google_refresh_token or refresh),
        },
    )


@router.get("/auth/me")
async def get_me(current: dict = Depends(get_current_user)):
    user = current["user"]
    return {
        "role": current["role"],
        "id": current["user_id"],
        "name": user.name,
        "email": getattr(user, "email", None),
        "hospital_id": current.get("hospital_id"),
        "patient_code": getattr(user, "patient_code", None),
        "hospital_code": getattr(user, "hospital_code", None),
        "address": getattr(user, "address", None),
        "phone": getattr(user, "phone", None),
        "city": getattr(user, "city", None),
    }
