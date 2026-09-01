from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, require_roles
from app.database import get_db
from app.models import Doctor, Patient, Receptionist
from app.services.proactive_monitor_service import get_last_proactive_scan, run_proactive_scan_all
from app.schemas.api import DoctorCreate, PatientCreate, ReceptionistCreate

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/doctors")
async def create_doctor(
    data: DoctorCreate,
    current: dict = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    hospital_id = current["hospital_id"]
    existing = await db.execute(
        select(Doctor).where(Doctor.email == data.email, Doctor.hospital_id == hospital_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Doctor email already exists")
    initials = "".join(w[0].upper() for w in data.name.split()[:2]) or "DR"
    doctor = Doctor(
        hospital_id=hospital_id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        specialization=data.specialization,
        gender=data.gender,
        doctor_code=initials[:3],
    )
    db.add(doctor)
    await db.flush()
    return {"id": doctor.id, "name": doctor.name, "doctor_code": doctor.doctor_code}


@router.post("/receptionists")
async def create_receptionist(
    data: ReceptionistCreate,
    current: dict = Depends(require_roles("admin")),
    db: AsyncSession = Depends(get_db),
):
    hospital_id = current["hospital_id"]
    rec = Receptionist(
        hospital_id=hospital_id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(rec)
    await db.flush()
    return {"id": rec.id, "name": rec.name}


@router.post("/patients")
async def create_patient(
    data: PatientCreate,
    current: dict = Depends(require_roles("receptionist", "admin")),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date
    hospital_id = current["hospital_id"]
    patient_code = f"PAT-{date.today().strftime('%Y%m%d')}-{uuid4().hex[:4].upper()}"
    patient = Patient(
        patient_code=patient_code,
        doctor_id=data.doctor_id,
        hospital_id=hospital_id,
        name=data.name,
        age=data.age,
        gender=data.gender,
        contact=data.contact,
        email=data.email,
        disease=data.disease,
        visit_date=data.visit_date or date.today().isoformat(),
        blood_group=data.blood_group,
        weight_kg=data.weight_kg,
        blood_pressure=data.blood_pressure,
    )
    db.add(patient)
    await db.flush()
    return {"id": patient.id, "patient_code": patient.patient_code, "name": patient.name}


@router.post("/proactive-scan")
async def trigger_proactive_scan(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles("admin")),
):
    """Manually run the proactive Health Guardian scan (same as the background scheduler)."""
    result = await run_proactive_scan_all(db)
    return result


@router.get("/proactive-status")
async def proactive_monitor_status(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles("admin")),
):
    """Last proactive scan summary and scheduler settings."""
    from app.config import get_settings

    settings = get_settings()
    last = await get_last_proactive_scan(db)
    return {
        "enabled": settings.guardian_proactive_enabled,
        "scan_interval_hours": settings.guardian_scan_interval_hours,
        "silence_alert_days": settings.guardian_silence_alert_days,
        "last_scan": last,
    }
