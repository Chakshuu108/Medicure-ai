import asyncio
import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.events import AgentEventEmitter
from app.core.security import get_current_user, require_roles
from app.database import get_db
from app.models import (
    Alert,
    ChatMessage,
    Doctor,
    MCQResponse,
    MCQSet,
    Medicine,
    MeetSummary,
    OPDBooking,
    OPDSlot,
    Patient,
    Prescription,
)
from app.schemas.api import BookSlotRequest, ChatRequest, MCQSubmit, MeetSummaryCreate, OPDSlotCreate, PrescriptionCreate, SessionInitRequest, TranscriptLineCreate
from app.services.agent_service import AgentWorkflowService
from app.services.proactive_monitor_service import get_last_proactive_scan
from app.services.mcq_service import (
    compute_status,
    compute_total_score,
    extract_response_details,
    generate_today_mcqs,
    get_feedback,
    get_mcq_trends,
)
from app.services.email_service import send_booking_confirmation_email, send_worsening_alert_email
from app.services.alert_service import (
    collapse_duplicate_open_alerts,
    create_clinical_alert,
    is_doctor_facing,
    serialize_alert,
)
from app.services.reminder_service import process_missed_mcq_reminders
from app.services.guardian_service import run_guardian
from app.services.meet_service import (
    _assert_booking_access,
    clear_transcript_lines,
    format_transcript_lines,
    generate_meet_summary,
    get_transcript_lines,
    list_meet_summaries,
    save_transcript_line,
    slot_room_name,
)
from app.services.opd_booking_service import ensure_patient_can_book
from app.services.scheduling_service import frequency_label, get_patient_google_access_token, medicine_to_dict
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["clinical"])
settings = get_settings()


# ── Chat with SSE agent events ────────────────────────────────────────────────

@router.post("/patient/chat")
async def patient_chat(
    data: ChatRequest,
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    patient_id = current["user_id"]
    emitter = AgentEventEmitter()
    service = AgentWorkflowService(db)

    async def event_stream():
        queue = emitter.subscribe()

        async def run_workflow():
            return await service.run_chat(patient_id, data.message, emitter)

        task = asyncio.create_task(run_workflow())

        yield f"data: {json.dumps({'type': 'workflow_started', 'agent': 'orchestrator', 'status': 'running'})}\n\n"

        # Stream events in real-time while workflow runs
        while not task.done():
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.3)
                yield f"data: {json.dumps(event)}\n\n"
            except asyncio.TimeoutError:
                continue

        # Drain any remaining events
        while not queue.empty():
            event = queue.get_nowait()
            yield f"data: {json.dumps(event)}\n\n"

        result = await task
        yield f"data: {json.dumps({'type': 'chat_result', 'result': result})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/patient/guardian-check")
async def guardian_check(
    force: bool = Query(False),
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    patient_id = current["user_id"]
    result = await run_guardian(db, patient_id, force=force)
    return result


@router.get("/patient/guardian/latest")
async def guardian_latest(
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    return await run_guardian(db, current["user_id"], force=False)


@router.post("/patient/session-init")
async def patient_session_init(
    data: SessionInitRequest | None = None,
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    patient = current["user"]
    token = (data.google_access_token if data else None) or await get_patient_google_access_token(patient)
    reminders = await process_missed_mcq_reminders(db, patient, google_access_token=token)
    guardian = await run_guardian(db, patient.id, force=False)
    trends = await get_mcq_trends(db, patient.id, days=30)
    proactive = await get_last_proactive_scan(db)
    return {"guardian": guardian, "reminders": reminders, "trends": trends, "proactive_monitor": proactive}


@router.get("/patient/care-autopilot")
async def care_autopilot_dashboard(
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    """Autonomous care dashboard — aggregated agent outputs for the patient."""
    from app.services.scheduling_service import get_schedule_preview

    patient = current["user"]
    guardian = await run_guardian(db, patient.id, force=False)
    trends = await get_mcq_trends(db, patient.id, days=14)
    reminders = await process_missed_mcq_reminders(db, patient)
    proactive = await get_last_proactive_scan(db)
    schedule = await get_schedule_preview(db, patient.id)

    alert_result = await db.execute(
        select(Alert).where(Alert.patient_id == patient.id, Alert.resolved == False)
        .order_by(Alert.created_at.desc()).limit(5)
    )
    alerts = [serialize_alert(a, patient_name=patient.name) for a in alert_result.scalars()]

    booking_result = await db.execute(
        select(OPDBooking).options(selectinload(OPDBooking.slot))
        .where(OPDBooking.patient_id == patient.id)
        .order_by(OPDBooking.created_at.desc()).limit(3)
    )
    bookings = [{
        "slot_date": b.slot.slot_date if b.slot else "",
        "start_time": b.slot.start_time if b.slot else "",
        "room": slot_room_name(b.slot.id) if b.slot else "",
        "status": b.status,
    } for b in booking_result.scalars()]

    priorities: list[str] = []
    t_summary = trends.get("summary") or {}
    if t_summary.get("missed_days", 0) > 0:
        priorities.append(f"Complete your daily health check — {t_summary['missed_days']} day(s) missed recently.")
    if reminders.get("missed_dates"):
        priorities.append("Catch up on missed check-in days from the past two weeks.")
    if (guardian.get("actions") or {}).get("alerts_sent", 0) > 0:
        priorities.append("Your doctor was notified about a health pattern — check Alerts.")
    if not priorities:
        priorities.append("You're on track. Keep taking medicines on time and log daily check-ins.")

    autonomous_actions: list[str] = []
    if reminders.get("emails_sent"):
        autonomous_actions.append(f"Sent {reminders['emails_sent']} missed check-in reminder email(s)")
    if reminders.get("calendar_events"):
        autonomous_actions.append(f"Added {reminders['calendar_events']} calendar reminder(s)")
    if proactive:
        autonomous_actions.append("Background Health Guardian scan is running 24/7")
    if (guardian.get("actions") or {}).get("alerts_sent"):
        autonomous_actions.append("Notified your doctor about a health concern")

    reasoning = guardian.get("reasoning") or {}
    return {
        "status": "monitoring",
        "patient_message": reasoning.get("patient_message") or reasoning.get("overall_assessment") or "Your care team is watching your health.",
        "priorities": priorities,
        "autonomous_actions": autonomous_actions or ["Autonomous monitoring is active"],
        "trends": trends,
        "alerts": alerts,
        "upcoming_meds": schedule[:5],
        "bookings": bookings,
        "proactive_monitor": proactive,
        "guardian": guardian,
    }


@router.get("/patient/chat/history")
async def chat_history(current: dict = Depends(require_roles("patient")), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatMessage).where(ChatMessage.patient_id == current["user_id"])
        .order_by(ChatMessage.created_at.asc()).limit(50)
    )
    return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in result.scalars()]


# ── Prescriptions ─────────────────────────────────────────────────────────────

@router.post("/prescriptions")
async def create_prescription(
    data: PrescriptionCreate,
    current: dict = Depends(require_roles("doctor")),
    db: AsyncSession = Depends(get_db),
):
    doctor = current["user"]
    patient_result = await db.execute(select(Patient).where(Patient.id == data.patient_id))
    patient = patient_result.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    if patient.doctor_id != doctor.id:
        raise HTTPException(403, "This patient is not assigned to you")

    diagnosis = (data.disease or "").strip()
    if diagnosis:
        patient.disease = diagnosis

    rx = Prescription(
        patient_id=data.patient_id,
        doctor_id=doctor.id,
        disease=diagnosis,
        doctor_notes=data.doctor_notes,
    )
    db.add(rx)
    await db.flush()
    for med in data.medicines:
        if not med.name.strip():
            continue
        med_disease = (med.disease or diagnosis).strip()
        db.add(Medicine(
            prescription_id=rx.id,
            name=med.name.strip(),
            disease=med_disease,
            dosage=med.dosage,
            duration_days=med.duration_days,
            frequency_pattern=med.frequency_pattern,
            times_per_day=med.times_per_day,
            timing=frequency_label(med.frequency_pattern),
            start_date="",
            start_time="",
            dose_times="",
        ))
    await db.flush()
    return {"id": rx.id, "message": "Prescription created"}


@router.get("/prescriptions/patient/{patient_id}")
async def get_patient_prescriptions(patient_id: str, current: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Prescription).options(selectinload(Prescription.medicines))
        .where(Prescription.patient_id == patient_id).order_by(Prescription.created_at.desc())
    )
    rxs = result.scalars().all()
    return [{
        "id": r.id,
        "disease": r.disease,
        "doctor_notes": r.doctor_notes,
        "created_at": r.created_at.isoformat(),
        "medicines": [medicine_to_dict(m) for m in r.medicines],
    } for r in rxs]


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.get("/alerts")
async def get_alerts(current: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    role = current["role"]
    if role == "doctor":
        await collapse_duplicate_open_alerts(db, doctor_id=current["user_id"])
    elif role == "patient":
        await collapse_duplicate_open_alerts(db, patient_id=current["user_id"])

    if role == "patient":
        q = select(Alert).where(Alert.patient_id == current["user_id"])
    elif role == "doctor":
        q = (
            select(Alert)
            .join(Patient, Alert.patient_id == Patient.id)
            .where(
                or_(
                    Alert.doctor_id == current["user_id"],
                    Patient.doctor_id == current["user_id"],
                )
            )
        )
    else:
        q = select(Alert)

    result = await db.execute(
        q.where(Alert.resolved == False).order_by(Alert.created_at.desc()).limit(50)  # noqa: E712
    )
    alerts = [a for a in result.unique().scalars() if is_doctor_facing(a.alert_type)]

    patient_ids = {a.patient_id for a in alerts}
    patients_map: dict[str, Patient] = {}
    if patient_ids:
        pat_result = await db.execute(select(Patient).where(Patient.id.in_(patient_ids)))
        patients_map = {p.id: p for p in pat_result.scalars()}

    return [
        serialize_alert(
            a,
            patient_name=patients_map[a.patient_id].name if a.patient_id in patients_map else None,
            patient_code=patients_map[a.patient_id].patient_code if a.patient_id in patients_map else None,
        )
        for a in alerts
    ]


@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, current: dict = Depends(require_roles("doctor")), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.resolved = True
    return {"message": "Alert resolved"}


# ── OPD ───────────────────────────────────────────────────────────────────────

@router.post("/opd/slots")
async def create_opd_slots(data: OPDSlotCreate, current: dict = Depends(require_roles("doctor")), db: AsyncSession = Depends(get_db)):
    """Create exactly 5 consecutive OPD slots (10-minute blocks) for the doctor on the given date."""
    doctor_id = current["user_id"]
    slot_count = 5
    duration_minutes = 10

    last_result = await db.execute(
        select(OPDSlot)
        .where(OPDSlot.doctor_id == doctor_id, OPDSlot.slot_date == data.slot_date)
        .order_by(OPDSlot.end_time.desc())
        .limit(1)
    )
    last_slot = last_result.scalar_one_or_none()
    base_time = (
        datetime.strptime(last_slot.end_time, "%H:%M")
        if last_slot
        else datetime.strptime("09:00", "%H:%M")
    )

    slots = []
    for i in range(slot_count):
        start = base_time + timedelta(minutes=i * duration_minutes)
        end = start + timedelta(minutes=duration_minutes)
        slot = OPDSlot(
            doctor_id=doctor_id, slot_date=data.slot_date,
            start_time=start.strftime("%H:%M"), end_time=end.strftime("%H:%M"),
        )
        db.add(slot)
        slots.append(slot)
    await db.flush()
    return {
        "created": len(slots),
        "slot_ids": [s.id for s in slots],
        "slots": [{
            "id": s.id,
            "slot_date": s.slot_date,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "room": slot_room_name(s.id),
        } for s in slots],
    }


@router.get("/opd/slots/mine")
async def doctor_slots(
    current: dict = Depends(require_roles("doctor")),
    db: AsyncSession = Depends(get_db),
):
    """All OPD slots for the logged-in doctor with shared video room links."""
    result = await db.execute(
        select(OPDSlot)
        .options(selectinload(OPDSlot.booking))
        .where(OPDSlot.doctor_id == current["user_id"])
        .order_by(OPDSlot.slot_date.desc(), OPDSlot.start_time)
    )
    slots = result.scalars().all()
    return [{
        "id": s.id,
        "slot_date": s.slot_date,
        "start_time": s.start_time,
        "end_time": s.end_time,
        "is_booked": s.is_booked,
        "room": slot_room_name(s.id),
        "booking_id": s.booking.id if s.booking else None,
        "patient_name": s.booking.patient_name if s.booking else None,
    } for s in slots]


@router.get("/opd/slots/available")
async def available_slots(doctor_id: str | None = None, slot_date: str | None = None,
                          current: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(OPDSlot).where(OPDSlot.is_booked == False)
    if doctor_id:
        q = q.where(OPDSlot.doctor_id == doctor_id)
    if slot_date:
        q = q.where(OPDSlot.slot_date == slot_date)
    result = await db.execute(q.order_by(OPDSlot.slot_date, OPDSlot.start_time))
    slots = result.scalars().all()
    doc_result = await db.execute(select(Doctor))
    doctors = {d.id: d.name for d in doc_result.scalars().all()}
    return [{
        "id": s.id, "doctor_id": s.doctor_id, "doctor_name": doctors.get(s.doctor_id, ""),
        "slot_date": s.slot_date, "start_time": s.start_time, "end_time": s.end_time,
        "room": slot_room_name(s.id),
    } for s in slots]


@router.post("/opd/book")
async def book_slot(data: BookSlotRequest, current: dict = Depends(require_roles("patient")), db: AsyncSession = Depends(get_db)):
    patient = current["user"]
    try:
        await ensure_patient_can_book(db, patient.id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    result = await db.execute(select(OPDSlot).where(OPDSlot.id == data.slot_id))
    slot = result.scalar_one_or_none()
    if not slot or slot.is_booked:
        raise HTTPException(400, "Slot unavailable")
    slot.is_booked = True
    booking = OPDBooking(slot_id=slot.id, patient_id=patient.id, patient_name=patient.name)
    db.add(booking)
    await db.flush()

    doc_result = await db.execute(select(Doctor).where(Doctor.id == slot.doctor_id))
    doctor = doc_result.scalar_one_or_none()
    if patient.email:
        await send_booking_confirmation_email(
            patient.name, patient.email, slot.slot_date, slot.start_time,
            doctor.name if doctor else "your doctor",
        )

    return {"booking_id": booking.id, "slot_date": slot.slot_date, "start_time": slot.start_time, "room": slot_room_name(slot.id)}


@router.get("/opd/booking-limit")
async def booking_limit(
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    from app.services.opd_booking_service import get_patient_active_booking

    active = await get_patient_active_booking(db, current["user_id"])
    return {
        "can_book": active is None,
        "active_booking": {
            "id": active.id,
            "slot_date": active.slot.slot_date if active and active.slot else "",
            "start_time": active.slot.start_time if active and active.slot else "",
            "room": slot_room_name(active.slot.id) if active and active.slot else "",
        } if active else None,
    }


@router.get("/opd/bookings")
async def my_bookings(current: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current["role"] == "patient":
        q = select(OPDBooking).options(selectinload(OPDBooking.slot)).where(OPDBooking.patient_id == current["user_id"])
    elif current["role"] == "doctor":
        q = (
            select(OPDBooking)
            .options(selectinload(OPDBooking.slot))
            .join(OPDSlot, OPDBooking.slot_id == OPDSlot.id)
            .where(OPDSlot.doctor_id == current["user_id"])
        )
    else:
        q = select(OPDBooking).options(selectinload(OPDBooking.slot))
    result = await db.execute(q.order_by(OPDBooking.created_at.desc()))
    return [{
        "id": b.id, "patient_name": b.patient_name, "status": b.status,
        "slot_date": b.slot.slot_date if b.slot else "", "start_time": b.slot.start_time if b.slot else "",
        "room": slot_room_name(b.slot.id) if b.slot else "",
        "slot_id": b.slot.id if b.slot else "",
    } for b in result.scalars()]


@router.post("/opd/transcript-line")
async def append_transcript_line(
    data: TranscriptLineCreate,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await _assert_booking_access(db, data.booking_id, current["role"], current["user_id"])
    except ValueError as exc:
        raise HTTPException(404 if "not found" in str(exc).lower() else 403, str(exc)) from exc
    await save_transcript_line(
        db,
        data.booking_id,
        data.speaker_label,
        data.text,
        data.timestamp_ms,
    )
    return {"ok": True}


@router.get("/opd/transcript/{booking_id}")
async def fetch_transcript_lines(
    booking_id: str,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await _assert_booking_access(db, booking_id, current["role"], current["user_id"])
    except ValueError as exc:
        raise HTTPException(404 if "not found" in str(exc).lower() else 403, str(exc)) from exc
    lines = await get_transcript_lines(db, booking_id)
    return {
        "lines": lines,
        "formatted": format_transcript_lines(lines),
        "count": len(lines),
    }


@router.post("/opd/meet-summary")
async def create_meet_summary(
    data: MeetSummaryCreate,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OPDBooking).where(OPDBooking.id == data.booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")
    role = current["role"]
    if role == "patient" and booking.patient_id != current["user_id"]:
        raise HTTPException(403, "Not your booking")
    if role == "doctor":
        slot = await db.execute(select(OPDSlot).where(OPDSlot.id == booking.slot_id))
        slot_row = slot.scalar_one_or_none()
        if not slot_row or slot_row.doctor_id != current["user_id"]:
            raise HTTPException(403, "Not your booking")
    try:
        summary = await generate_meet_summary(db, data.booking_id, data.transcript)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(500, f"Summary generation failed: {exc}") from exc
    return {"message": "Summary saved", "summary": summary}


@router.get("/opd/meet-summary/{booking_id}")
async def get_meet_summary_for_booking(
    booking_id: str,
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OPDBooking).where(OPDBooking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")
    if current["role"] == "patient" and booking.patient_id != current["user_id"]:
        raise HTTPException(403, "Not your booking")
    if current["role"] == "doctor":
        slot = await db.execute(select(OPDSlot).where(OPDSlot.id == booking.slot_id))
        slot_row = slot.scalar_one_or_none()
        if not slot_row or slot_row.doctor_id != current["user_id"]:
            raise HTTPException(403, "Not your booking")
    row = await db.execute(select(MeetSummary).where(MeetSummary.booking_id == booking_id))
    summary = row.scalar_one_or_none()
    if not summary:
        return {"summary": None}
    return {
        "summary": summary.summary_json,
        "created_at": summary.created_at.isoformat() if summary.created_at else "",
    }


@router.get("/opd/meet-summaries")
async def get_meet_summaries(
    current: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current["role"] not in ("patient", "doctor"):
        raise HTTPException(403, "Patients and doctors only")
    return await list_meet_summaries(db, role=current["role"], user_id=current["user_id"])


# ── MCQ ───────────────────────────────────────────────────────────────────────

@router.get("/mcq/today")
async def get_today_mcq(current: dict = Depends(require_roles("patient")), db: AsyncSession = Depends(get_db)):
    patient = current["user"]
    return await generate_today_mcqs(db, patient)


@router.post("/mcq/submit")
async def submit_mcq(data: MCQSubmit, current: dict = Depends(require_roles("patient")), db: AsyncSession = Depends(get_db)):
    patient = current["user"]
    today = date.today().isoformat()

    existing = await db.execute(
        select(MCQResponse).where(MCQResponse.patient_id == patient.id, MCQResponse.date == today)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "You already completed today's health check.")

    mcq_result = await db.execute(
        select(MCQSet).where(MCQSet.patient_id == patient.id, MCQSet.date == today)
    )
    mcq_set = mcq_result.scalar_one_or_none()
    questions = []
    if mcq_set:
        from app.services.mcq_service import _normalize_questions
        questions = _normalize_questions(mcq_set.questions_json)

    total_score = data.total_score
    if questions:
        total_score = compute_total_score(questions, data.responses)
    status = compute_status(total_score)
    _, adherence, side_effects = extract_response_details(questions, data.responses) if questions else ([], data.adherence_status, data.side_effects)

    response = MCQResponse(
        patient_id=patient.id, doctor_id=patient.doctor_id,
        date=today, responses_json=data.responses,
        total_score=total_score, status=status,
        side_effects=side_effects or data.side_effects,
        adherence_status=adherence or data.adherence_status,
    )
    db.add(response)
    feedback = get_feedback(status)

    if total_score < 0 or status == "Worsening":
        severity = "medium" if total_score >= -3 else "high"
        await create_clinical_alert(
            db,
            patient_id=patient.id,
            doctor_id=patient.doctor_id,
            alert_type="mcq_health_check",
            message=(
                f"Daily health check: status {status}, score {total_score}. "
                f"Adherence: {adherence or 'unknown'}."
                + (f" Side effects: {', '.join(side_effects)}." if side_effects else "")
            ),
            severity=severity,
        )
        if patient.email:
            try:
                asyncio.get_running_loop().create_task(
                    send_worsening_alert_email(patient.name, patient.email, status, total_score)
                )
            except RuntimeError:
                pass

    await db.flush()
    return {
        "message": "MCQ submitted",
        "score": total_score,
        "status": status,
        "feedback": feedback,
    }


@router.get("/mcq/history")
async def mcq_history(current: dict = Depends(require_roles("patient")), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MCQResponse).where(MCQResponse.patient_id == current["user_id"])
        .order_by(MCQResponse.date.desc()).limit(30)
    )
    return [{"date": r.date, "total_score": r.total_score, "status": r.status} for r in result.scalars()]


@router.get("/mcq/trends")
async def mcq_trends(
    days: int = 30,
    current: dict = Depends(require_roles("patient")),
    db: AsyncSession = Depends(get_db),
):
    return await get_mcq_trends(db, current["user_id"], days=min(days, 90))


# ── Patients & Doctors lists ──────────────────────────────────────────────────

@router.get("/patients")
async def list_patients(current: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    role = current["role"]
    if role == "doctor":
        q = select(Patient).where(Patient.doctor_id == current["user_id"])
    elif role in ("admin", "receptionist"):
        q = select(Patient).where(Patient.hospital_id == current["hospital_id"])
    elif role == "patient":
        q = select(Patient).where(Patient.id == current["user_id"])
    else:
        q = select(Patient)
    result = await db.execute(q.order_by(Patient.created_at.desc()))
    return [{
        "id": p.id, "patient_code": p.patient_code, "name": p.name, "age": p.age,
        "gender": p.gender, "disease": p.disease, "risk_level": p.risk_level,
        "risk_score": p.risk_score, "visit_date": p.visit_date,
        "contact": p.contact, "email": p.email,
        "blood_group": p.blood_group, "weight_kg": p.weight_kg, "height_cm": p.height_cm,
        "temperature_c": p.temperature_c, "pulse_bpm": p.pulse_bpm,
        "oxygen_spo2": p.oxygen_spo2, "blood_pressure": p.blood_pressure,
        "address": p.address,
    } for p in result.scalars()]


@router.get("/doctors")
async def list_doctors(hospital_id: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Doctor)
    if hospital_id:
        q = q.where(Doctor.hospital_id == hospital_id)
    result = await db.execute(q)
    return [{"id": d.id, "name": d.name, "specialization": d.specialization, "hospital_id": d.hospital_id} for d in result.scalars()]
