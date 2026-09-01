"""Seed demo data for MediCure platform."""

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

# Allow running as: python scripts/seed_demo.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.core.security import hash_password
from app.database import AsyncSessionLocal, Base, engine
from app.models import (
    Alert,
    ChatMessage,
    Doctor,
    Hospital,
    MCQResponse,
    Medicine,
    OPDSlot,
    Patient,
    Prescription,
    Receptionist,
)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(Hospital).where(Hospital.email == "admin@medicure.demo"))
        if existing.scalar_one_or_none():
            print("Demo data already exists. Skipping seed.")
            return

        hospital = Hospital(
            hospital_code="HOSP-DEMO",
            name="MediCure Demo Hospital",
            email="admin@medicure.demo",
            password_hash=hash_password("demo123"),
            address="123 Healthcare Avenue",
            phone="+91 98765 43210",
            city="Mumbai",
            pincode="400001",
        )
        db.add(hospital)
        await db.flush()

        doctor = Doctor(
            hospital_id=hospital.id,
            name="Dr. Priya Sharma",
            email="doctor@medicure.demo",
            password_hash=hash_password("demo123"),
            specialization="Internal Medicine",
            gender="Female",
            doctor_code="PSH",
        )
        db.add(doctor)
        await db.flush()

        receptionist = Receptionist(
            hospital_id=hospital.id,
            name="Ravi Kumar",
            email="reception@medicure.demo",
            password_hash=hash_password("demo123"),
        )
        db.add(receptionist)

        patient = Patient(
            patient_code="PAT-DEMO-0001",
            doctor_id=doctor.id,
            hospital_id=hospital.id,
            name="Amit Patel",
            age=42,
            gender="Male",
            contact="+91 99887 76655",
            email="amit.patel@demo.com",
            disease="Type 2 Diabetes, Hypertension",
            visit_date=date.today().isoformat(),
            risk_score=45,
            risk_level="medium",
            blood_group="B+",
            weight_kg=78.5,
            blood_pressure="130/85",
            pulse_bpm=78,
            oxygen_spo2=97.0,
        )
        db.add(patient)
        await db.flush()

        rx = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            doctor_notes="Continue current regimen. Monitor blood sugar weekly.",
        )
        db.add(rx)
        await db.flush()

        for med in [
            ("Metformin", "500mg", 30, "twice daily after meals"),
            ("Amlodipine", "5mg", 30, "morning"),
            ("Atorvastatin", "10mg", 30, "night"),
        ]:
            db.add(Medicine(
                prescription_id=rx.id, name=med[0], dosage=med[1],
                duration_days=med[2], timing=med[3], start_date=date.today().isoformat(),
            ))

        # OPD slots for next 3 days
        for day_offset in range(1, 4):
            slot_date = (date.today() + timedelta(days=day_offset)).isoformat()
            for hour in [9, 10, 11, 14, 15]:
                db.add(OPDSlot(
                    doctor_id=doctor.id,
                    slot_date=slot_date,
                    start_time=f"{hour:02d}:00",
                    end_time=f"{hour:02d}:17",
                ))

        # Sample MCQ history (last 6 days — today left open for demo missed check-in)
        for i in range(6):
            d = (date.today() - timedelta(days=6 - i)).isoformat()
            score = [-2, -1, 0, 1, 0, -1][i]
            status = "Worsening" if score <= -2 else "Stable" if score >= 0 else "Improving"
            db.add(MCQResponse(
                patient_id=patient.id, doctor_id=doctor.id, date=d,
                responses_json={"q1": "Fair"}, total_score=score, status=status,
                adherence_status="Good" if i % 2 == 0 else "Missed morning dose",
            ))

        db.add(Alert(
            patient_id=patient.id, doctor_id=doctor.id,
            alert_type="mcq_health_check",
            message="Patient MCQ score dropped to -3. Worsening trend detected.",
            severity="medium",
        ))

        db.add(ChatMessage(
            patient_id=patient.id, role="assistant",
            content="Welcome to MediCure! I'm your AI health assistant. How can I help you today?",
        ))

        await db.commit()
        print("Demo data seeded successfully!")
        print("\nDemo Credentials:")
        print("  Admin:        admin@medicure.demo / demo123")
        print("  Doctor:       doctor@medicure.demo / demo123")
        print("  Receptionist: reception@medicure.demo / demo123")
        print("  Patient:      PAT-DEMO-0001 (no password)")


if __name__ == "__main__":
    asyncio.run(seed())
