"""LangChain tools for agentic workflows."""

from datetime import date
from typing import Annotated

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Alert, ChatMessage, Doctor, Medicine, OPDBooking, OPDSlot, Patient, Prescription


def create_tools(db: AsyncSession, patient_id: str):
    """Factory that binds DB session and patient context to tools."""

    @tool
    async def get_patient_context() -> str:
        """Get full patient profile including risk, condition, and vitals."""
        result = await db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = result.scalar_one_or_none()
        if not patient:
            return "Patient not found."
        return (
            f"Name: {patient.name}, Age: {patient.age}, Gender: {patient.gender}, "
            f"Condition: {patient.disease}, Risk: {patient.risk_level} ({patient.risk_score}/100), "
            f"BP: {patient.blood_pressure}, Contact: {patient.contact}"
        )

    @tool
    async def get_prescriptions() -> str:
        """Get patient's current prescriptions and medicines."""
        result = await db.execute(
            select(Prescription)
            .options(selectinload(Prescription.medicines))
            .where(Prescription.patient_id == patient_id)
            .order_by(Prescription.created_at.desc())
        )
        prescriptions = result.scalars().all()
        if not prescriptions:
            return "No prescriptions found."
        lines = []
        for pr in prescriptions[:3]:
            meds = ", ".join(f"{m.name} {m.dosage} ({m.timing})" for m in pr.medicines)
            lines.append(f"Rx from {pr.created_at.date()}: {meds}. Notes: {pr.doctor_notes}")
        return "\n".join(lines)

    @tool
    async def get_chat_history(limit: int = 10) -> str:
        """Get recent chat history for context."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.patient_id == patient_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return "\n".join(f"{m.role}: {m.content[:200]}" for m in messages) or "No chat history."

    @tool
    async def get_active_alerts() -> str:
        """Get unresolved alerts for the patient."""
        result = await db.execute(
            select(Alert)
            .where(Alert.patient_id == patient_id, Alert.resolved == False)
            .order_by(Alert.created_at.desc())
        )
        alerts = result.scalars().all()
        if not alerts:
            return "No active alerts."
        return "\n".join(f"[{a.severity}] {a.alert_type}: {a.message[:150]}" for a in alerts)

    @tool
    async def search_available_slots(doctor_name: str = "", slot_date: str = "") -> str:
        """Search available OPD appointment slots. Optional filters: doctor_name, slot_date (YYYY-MM-DD)."""
        query = (
            select(OPDSlot)
            .where(OPDSlot.is_booked == False)
            .options(selectinload(OPDSlot.booking))
        )
        if slot_date:
            query = query.where(OPDSlot.slot_date == slot_date)
        result = await db.execute(query.order_by(OPDSlot.slot_date, OPDSlot.start_time).limit(20))
        slots = result.scalars().all()
        if not slots:
            return "No available slots found."
        from app.services.meet_service import slot_room_name
        doc_result = await db.execute(select(Doctor))
        doctors = {d.id: d.name for d in doc_result.scalars().all()}
        lines = []
        for i, s in enumerate(slots, 1):
            doc_name = doctors.get(s.doctor_id, "Unknown")
            if doctor_name and doctor_name.lower() not in doc_name.lower():
                continue
            room = slot_room_name(s.id)
            lines.append(
                f"{i}. Dr. {doc_name} on {s.slot_date} at {s.start_time} (room: {room}, slot_id: {s.id})"
            )
        return "\n".join(lines) if lines else "No matching slots."

    @tool
    async def book_appointment(slot_id: str) -> str:
        """Book an OPD appointment by slot_id."""
        result = await db.execute(select(OPDSlot).where(OPDSlot.id == slot_id))
        slot = result.scalar_one_or_none()
        if not slot:
            return f"Slot {slot_id} not found."
        if slot.is_booked:
            return f"Slot {slot_id} is already booked."
        patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = patient_result.scalar_one_or_none()
        if not patient:
            return "Patient not found."
        from app.services.opd_booking_service import ensure_patient_can_book
        try:
            await ensure_patient_can_book(db, patient_id)
        except ValueError as exc:
            return str(exc)
        slot.is_booked = True
        booking = OPDBooking(
            slot_id=slot.id,
            patient_id=patient_id,
            patient_name=patient.name,
            status="confirmed",
        )
        db.add(booking)
        await db.flush()
        from app.services.meet_service import slot_room_name
        room = slot_room_name(slot.id)
        return (
            f"Successfully booked on {slot.slot_date} at {slot.start_time}. "
            f"Video room: {room}. Booking ID: {booking.id}"
        )

    @tool
    async def cancel_appointment(booking_id: str) -> str:
        """Cancel an OPD booking by booking_id."""
        result = await db.execute(
            select(OPDBooking)
            .options(selectinload(OPDBooking.slot))
            .where(OPDBooking.id == booking_id, OPDBooking.patient_id == patient_id)
        )
        booking = result.scalar_one_or_none()
        if not booking:
            return f"Booking {booking_id} not found."
        booking.status = "cancelled"
        if booking.slot:
            booking.slot.is_booked = False
        await db.flush()
        return f"Booking {booking_id} cancelled successfully."

    @tool
    async def create_alert(alert_type: str, message: str, severity: str = "medium") -> str:
        """Create a clinical alert for the patient's doctor."""
        from app.services.alert_service import create_clinical_alert

        patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = patient_result.scalar_one_or_none()
        if not patient:
            return "Patient not found."
        await create_clinical_alert(
            db,
            patient_id=patient_id,
            doctor_id=patient.doctor_id,
            alert_type=alert_type,
            message=message,
            severity=severity,
        )
        return f"Alert created and sent to doctor: {alert_type} ({severity})"

    @tool
    async def update_risk_score(score: int, level: str, reasoning: str) -> str:
        """Update patient risk score (0-100) and level (low/medium/high)."""
        result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = result.scalar_one_or_none()
        if not patient:
            return "Patient not found."
        patient.risk_score = max(0, min(100, score))
        patient.risk_level = level
        await db.flush()
        return f"Risk updated to {level} ({patient.risk_score}/100). Reason: {reasoning}"

    return [
        get_patient_context,
        get_prescriptions,
        get_chat_history,
        get_active_alerts,
        search_available_slots,
        book_appointment,
        cancel_appointment,
        create_alert,
        update_risk_score,
    ]
