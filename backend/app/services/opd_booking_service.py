"""Smart OPD booking helpers for the chat scheduling agent."""

from __future__ import annotations

import re

from langchain_core.messages import AIMessage, BaseMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Doctor, OPDBooking, OPDSlot, Patient
from app.services.meet_service import slot_room_name

UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.I,
)

ACTIVE_BOOKING_STATUSES = frozenset({"confirmed", "pending"})


async def get_patient_active_booking(db: AsyncSession, patient_id: str) -> OPDBooking | None:
    """Return the patient's current non-cancelled OPD booking, if any."""
    result = await db.execute(
        select(OPDBooking)
        .options(selectinload(OPDBooking.slot))
        .where(
            OPDBooking.patient_id == patient_id,
            OPDBooking.status.in_(ACTIVE_BOOKING_STATUSES),
        )
        .order_by(OPDBooking.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


async def patient_can_book(db: AsyncSession, patient_id: str) -> bool:
    return await get_patient_active_booking(db, patient_id) is None


async def ensure_patient_can_book(db: AsyncSession, patient_id: str) -> None:
    existing = await get_patient_active_booking(db, patient_id)
    if existing:
        slot = existing.slot
        when = f"{slot.slot_date} at {slot.start_time}" if slot else "your existing slot"
        raise ValueError(
            f"You already have an active appointment ({when}). "
            "Cancel it before booking another slot."
        )


def _wants_booking(message: str) -> bool:
    msg = message.lower()
    if "cancel" in msg:
        return False
    return any(w in msg for w in ("book", "reserve", "confirm", "take", "schedule me", "pick"))


def _wants_cancel(message: str) -> bool:
    msg = message.lower()
    return "cancel" in msg and any(
        w in msg for w in ("booking", "appointment", "slot", "opd", "my", "it", "this")
    )


async def cancel_patient_active_booking(db: AsyncSession, patient_id: str) -> str:
    """Cancel the patient's current active OPD booking."""
    booking = await get_patient_active_booking(db, patient_id)
    if not booking:
        return "You don't have an active OPD booking to cancel."
    slot = booking.slot
    when = f"{slot.slot_date} at {slot.start_time}" if slot else "your appointment"
    booking.status = "cancelled"
    if slot:
        slot.is_booked = False
    await db.flush()
    return (
        f"Your appointment on **{when}** has been cancelled.\n\n"
        "The slot is now available again. You can book a new time whenever you're ready."
    )


async def smart_cancel_from_context(
    db: AsyncSession,
    *,
    patient_id: str,
    user_message: str,
) -> str | None:
    """Rule-based cancel: 'cancel my booking' without needing a booking ID."""
    if not _wants_cancel(user_message):
        return None
    return await cancel_patient_active_booking(db, patient_id)


def format_slots_for_chat(slots: list[OPDSlot], doctors: dict[str, str]) -> str:
    if not slots:
        return "No available appointment slots right now. Please check again later."
    lines = ["Here are the available OPD slots:\n"]
    for i, slot in enumerate(slots, 1):
        doc = doctors.get(slot.doctor_id, "Doctor")
        room = slot_room_name(slot.id)
        lines.append(
            f"{i}. **{slot.slot_date}** at **{slot.start_time}** with Dr. {doc}\n"
            f"   Video room: `{room}`\n"
            f"   Slot ID: `{slot.id}`"
        )
    lines.append(
        '\nTo book, say **"book the first slot"** or **"book slot 2"** — '
        "or tell me the slot ID."
    )
    return "\n".join(lines)


async def list_available_slots(
    db: AsyncSession,
    *,
    slot_date: str = "",
    limit: int = 10,
) -> list[OPDSlot]:
    q = select(OPDSlot).where(OPDSlot.is_booked == False)
    if slot_date:
        q = q.where(OPDSlot.slot_date == slot_date)
    result = await db.execute(q.order_by(OPDSlot.slot_date, OPDSlot.start_time).limit(limit))
    return list(result.scalars().all())


async def book_slot_for_patient(
    db: AsyncSession,
    *,
    patient_id: str,
    slot: OPDSlot,
) -> OPDBooking:
    patient_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise ValueError("Patient not found")
    await ensure_patient_can_book(db, patient_id)
    if slot.is_booked:
        raise ValueError("Slot already booked")
    slot.is_booked = True
    booking = OPDBooking(
        slot_id=slot.id,
        patient_id=patient_id,
        patient_name=patient.name,
        status="confirmed",
    )
    db.add(booking)
    await db.flush()
    return booking


def format_booking_confirmation(
    slot: OPDSlot,
    doctor_name: str,
    booking_id: str,
) -> str:
    room = slot_room_name(slot.id)
    return (
        f"Your appointment is confirmed!\n\n"
        f"**Doctor:** Dr. {doctor_name}\n"
        f"**Date:** {slot.slot_date}\n"
        f"**Time:** {slot.start_time}\n"
        f"**Video room:** `{room}`\n\n"
        f"Go to the **OPD Booking** tab to join the video call. "
        f"Your doctor uses the **same room link** for this time slot.\n\n"
        f"Booking reference: `{booking_id}`"
    )


async def smart_book_from_context(
    db: AsyncSession,
    *,
    patient_id: str,
    user_message: str,
    messages: list[BaseMessage],
) -> str | None:
    """Rule-based booking: first slot, slot N, or slot ID from chat history."""
    if not _wants_booking(user_message):
        return None

    if not await patient_can_book(db, patient_id):
        existing = await get_patient_active_booking(db, patient_id)
        slot = existing.slot if existing else None
        when = f"{slot.slot_date} at {slot.start_time}" if slot else "already booked"
        return (
            f"You already have an active appointment on **{when}**.\n\n"
            "You can only hold **one OPD slot** at a time. "
            "Cancel your current booking before reserving another."
        )

    msg = user_message.lower()
    slot: OPDSlot | None = None

    num_match = re.search(r"(?:slot|number|#)\s*(\d+)", msg)
    if num_match:
        idx = int(num_match.group(1)) - 1
        slots = await list_available_slots(db)
        if 0 <= idx < len(slots):
            slot = slots[idx]

    if not slot and re.search(r"(very\s+)?first|earliest|1st", msg):
        slots = await list_available_slots(db, limit=1)
        slot = slots[0] if slots else None

    if not slot:
        for uid in UUID_RE.findall(user_message):
            result = await db.execute(
                select(OPDSlot).where(OPDSlot.id == uid, OPDSlot.is_booked == False)
            )
            slot = result.scalar_one_or_none()
            if slot:
                break

    if not slot:
        for m in reversed(messages):
            if not isinstance(m, AIMessage):
                continue
            text = m.content if isinstance(m.content, str) else str(m.content or "")
            for uid in UUID_RE.findall(text):
                result = await db.execute(
                    select(OPDSlot).where(OPDSlot.id == uid, OPDSlot.is_booked == False)
                )
                slot = result.scalar_one_or_none()
                if slot:
                    break
            if slot:
                break

    if not slot:
        return None

    booking = await book_slot_for_patient(db, patient_id=patient_id, slot=slot)
    doc_result = await db.execute(select(Doctor).where(Doctor.id == slot.doctor_id))
    doctor = doc_result.scalar_one_or_none()
    return format_booking_confirmation(
        slot,
        doctor.name if doctor else "your doctor",
        booking.id,
    )
