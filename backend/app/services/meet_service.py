"""Post-call consultation summary generation via Groq."""

from __future__ import annotations

import json

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings, is_groq_configured
from app.models import MeetSummary, MeetTranscriptLine, OPDBooking, OPDSlot

SUMMARY_PROMPT = """You are a medical summarization assistant for MediCore.

Return ONLY valid JSON in this format:
{
  "sufferings": ["symptoms or complaints"],
  "disease": "diagnosed or suspected condition",
  "medicines_recommended": [
    {"medicine": "", "dose": "", "frequency": "", "duration": "", "notes": ""}
  ],
  "medicine_changes": "changes to existing meds or empty string",
  "conclusion": "2-4 sentence consultation conclusion",
  "precautions": ["precautions"],
  "follow_up": "follow-up instruction",
  "lifestyle_advice": {"dos": [], "donts": []}
}

Transcript:
"""


def slot_room_name(slot_id: str) -> str:
    """Persistent Jitsi room per OPD slot — same link for doctor and patient."""
    safe = slot_id.replace("-", "").replace(" ", "")
    return f"MediCure-{safe[:20]}"


def booking_room_name(booking_id: str) -> str:
    """Legacy helper — prefer slot_room_name when slot_id is known."""
    safe = booking_id.replace("-", "").replace(" ", "")
    return f"MediCure-{safe}"


async def _assert_booking_access(db: AsyncSession, booking_id: str, role: str, user_id: str) -> OPDBooking:
    result = await db.execute(select(OPDBooking).where(OPDBooking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise ValueError("Booking not found")
    if role == "patient" and booking.patient_id != user_id:
        raise ValueError("Not your booking")
    if role == "doctor":
        slot = await db.execute(select(OPDSlot).where(OPDSlot.id == booking.slot_id))
        slot_row = slot.scalar_one_or_none()
        if not slot_row or slot_row.doctor_id != user_id:
            raise ValueError("Not your booking")
    return booking


async def save_transcript_line(
    db: AsyncSession,
    booking_id: str,
    speaker_label: str,
    text: str,
    timestamp_ms: int = 0,
) -> None:
    cleaned = text.strip()
    if len(cleaned) < 2:
        return
    db.add(MeetTranscriptLine(
        booking_id=booking_id,
        speaker_label=speaker_label.strip() or "Speaker",
        text=cleaned,
        timestamp_ms=timestamp_ms,
    ))
    await db.flush()


async def get_transcript_lines(db: AsyncSession, booking_id: str) -> list[dict]:
    result = await db.execute(
        select(MeetTranscriptLine)
        .where(MeetTranscriptLine.booking_id == booking_id)
        .order_by(MeetTranscriptLine.timestamp_ms.asc(), MeetTranscriptLine.created_at.asc())
    )
    return [
        {
            "speaker_label": row.speaker_label,
            "text": row.text,
            "timestamp_ms": row.timestamp_ms,
        }
        for row in result.scalars().all()
    ]


def format_transcript_lines(lines: list[dict]) -> str:
    return "\n".join(f"{line['speaker_label']}: {line['text']}" for line in lines if line.get("text"))


async def clear_transcript_lines(db: AsyncSession, booking_id: str) -> None:
    result = await db.execute(select(MeetTranscriptLine).where(MeetTranscriptLine.booking_id == booking_id))
    for row in result.scalars().all():
        db.delete(row)
    await db.flush()


async def generate_meet_summary(db: AsyncSession, booking_id: str, transcript: str) -> dict:
    cleaned = transcript.strip()
    if not cleaned or len(cleaned) < 15:
        lines = await get_transcript_lines(db, booking_id)
        cleaned = format_transcript_lines(lines).strip()
    if not cleaned or len(cleaned) < 15:
        raise ValueError("Transcript too short. Speak during the call or type consultation notes (at least a few sentences).")

    if not is_groq_configured():
        raise ValueError("GROQ_API_KEY not configured in backend/.env")

    result = await db.execute(
        select(OPDBooking).options(selectinload(OPDBooking.slot)).where(OPDBooking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking or not booking.slot:
        raise ValueError("Booking not found")

    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": SUMMARY_PROMPT + cleaned}],
                    "temperature": 0.2,
                    "max_tokens": 1500,
                },
            )
            resp.raise_for_status()
            message = resp.json()["choices"][0]["message"]
            raw = (message.get("content") or message.get("reasoning") or "").strip()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:200] if exc.response else str(exc)
        raise ValueError(f"AI service error ({exc.response.status_code}): {detail}") from exc
    except Exception as exc:
        raise ValueError(f"AI service error: {exc}") from exc

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        summary = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI returned invalid JSON: {exc}") from exc

    existing = await db.execute(select(MeetSummary).where(MeetSummary.booking_id == booking_id))
    row = existing.scalar_one_or_none()
    if row:
        row.transcript = cleaned
        row.summary_json = summary
    else:
        db.add(MeetSummary(
            booking_id=booking_id,
            doctor_id=booking.slot.doctor_id,
            patient_id=booking.patient_id,
            transcript=cleaned,
            summary_json=summary,
        ))
    await clear_transcript_lines(db, booking_id)
    await db.flush()
    return summary


async def list_meet_summaries(db: AsyncSession, *, role: str, user_id: str) -> list[dict]:
    q = (
        select(MeetSummary, OPDBooking, OPDSlot)
        .join(OPDBooking, MeetSummary.booking_id == OPDBooking.id)
        .join(OPDSlot, OPDBooking.slot_id == OPDSlot.id)
        .order_by(MeetSummary.created_at.desc())
    )
    if role == "patient":
        q = q.where(MeetSummary.patient_id == user_id)
    elif role == "doctor":
        q = q.where(MeetSummary.doctor_id == user_id)

    result = await db.execute(q)
    rows = []
    for summary, booking, slot in result.all():
        rows.append({
            "id": summary.id,
            "booking_id": summary.booking_id,
            "patient_name": booking.patient_name,
            "slot_date": slot.slot_date,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "summary_json": summary.summary_json,
            "created_at": summary.created_at.isoformat() if summary.created_at else "",
        })
    return rows
