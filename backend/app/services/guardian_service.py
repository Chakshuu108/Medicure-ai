"""Health Guardian — full perceive → reason → act loop."""

import json
from collections import defaultdict
from datetime import date, datetime, timedelta

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents.graph.workflow import _extract_content
from app.config import get_settings, is_groq_configured
from app.models import AgentRun, Alert, MCQResponse, OPDBooking, OPDSlot, Patient, Prescription
from app.services.alert_service import create_clinical_alert

DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


async def _perceive(db: AsyncSession, patient: Patient) -> dict:
    mcq_result = await db.execute(
        select(MCQResponse)
        .where(MCQResponse.patient_id == patient.id)
        .order_by(MCQResponse.date.asc())
        .limit(30)
    )
    responses = list(mcq_result.scalars().all())

    alert_result = await db.execute(
        select(Alert).where(Alert.patient_id == patient.id).order_by(Alert.created_at.desc()).limit(50)
    )
    alerts = list(alert_result.scalars().all())

    rx_result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.medicines))
        .where(Prescription.patient_id == patient.id)
        .order_by(Prescription.created_at.desc())
    )
    prescriptions = list(rx_result.scalars().all())

    booking_result = await db.execute(
        select(OPDBooking)
        .options(selectinload(OPDBooking.slot))
        .where(OPDBooking.patient_id == patient.id)
        .order_by(OPDBooking.created_at.desc())
    )
    bookings = list(booking_result.scalars().all())

    dow_scores: dict[int, list] = defaultdict(list)
    dow_dates: dict[int, list] = defaultdict(list)
    for r in responses:
        try:
            d = datetime.strptime(r.date, "%Y-%m-%d")
            dow_scores[d.weekday()].append(r.total_score)
            dow_dates[d.weekday()].append(r.date)
        except ValueError:
            pass

    timeline = sorted(responses, key=lambda x: x.date)
    scores = [r.total_score for r in timeline]
    dates = [r.date for r in timeline]
    statuses = [r.status for r in timeline]

    missed_dates = []
    for r in timeline:
        adh = (r.adherence_status or "").lower()
        if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no", "partial"]):
            missed_dates.append(r.date)

    med_schedule = []
    for pr in prescriptions:
        for m in pr.medicines:
            med_schedule.append({"name": m.name, "frequency": m.timing})

    guardian_alerts = [
        a for a in alerts
        if "Health Guardian" in (a.alert_type or "") or "Guardian" in (a.message or "")
    ]
    already_flagged = [a.message[:60] for a in guardian_alerts]

    today_str = date.today().isoformat()
    upcoming = None
    for b in bookings:
        slot = b.slot
        if slot and slot.slot_date >= today_str and b.status not in ("cancelled",):
            upcoming = {
                "slot_date": slot.slot_date,
                "start_time": slot.start_time,
                "status": b.status,
            }
            break

    last_checkin = dates[-1] if dates else None
    days_silent = 0
    if last_checkin:
        try:
            days_silent = (date.today() - datetime.strptime(last_checkin, "%Y-%m-%d").date()).days
        except ValueError:
            pass

    doctor_name = "Your Doctor"
    if patient.doctor:
        doctor_name = patient.doctor.name

    return {
        "patient_id": patient.id,
        "name": patient.name,
        "disease": patient.disease or "",
        "doctor_id": patient.doctor_id,
        "doctor_name": doctor_name,
        "scores": scores,
        "dates": dates,
        "statuses": statuses,
        "missed_dates": missed_dates,
        "med_schedule": med_schedule,
        "dow_scores": {str(k): v for k, v in dow_scores.items()},
        "dow_dates": {str(k): v for k, v in dow_dates.items()},
        "already_flagged": already_flagged,
        "upcoming": upcoming,
        "days_silent": days_silent,
        "checkin_count": len(responses),
        "today": today_str,
        "unresolved_alerts": len([a for a in alerts if not a.resolved]),
        "risk_level": patient.risk_level,
        "risk_score": patient.risk_score,
    }


async def _reason(snapshot: dict) -> dict:
    if not is_groq_configured():
        return {
            "findings": [],
            "overall_assessment": "Health Guardian requires a Groq API key.",
            "patient_message": "Configure your AI key to enable autonomous monitoring.",
            "actions_taken_summary": "No actions taken.",
        }

    dow_summary = {}
    for k, v in snapshot["dow_scores"].items():
        if v:
            avg = round(sum(v) / len(v), 1)
            dow_summary[DOW[int(k)]] = {"avg_score": avg, "n": len(v)}

    settings = get_settings()
    llm = ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model, temperature=0.25)

    system = """You are Health Guardian — autonomous cross-session health monitoring AI.
Respond ONLY with valid JSON:
{
  "findings": [{
    "type": "pattern|anomaly|silence|escalation|medication_effect",
    "title": "short title",
    "description": "1-2 sentences",
    "reasoning_chain": ["step1","step2","step3"],
    "severity": "low|medium|high",
    "action": "alert_doctor|flag_in_brief|monitor|none",
    "alert_message": "clinical note for doctor if alerting"
  }],
  "overall_assessment": "one sentence",
  "patient_message": "warm one sentence for patient",
  "actions_taken_summary": "what you would do"
}
Do not repeat already_flagged items. Be specific with dates and scores."""

    upcoming = snapshot.get("upcoming")
    appt_str = f"{upcoming['slot_date']} at {upcoming['start_time']}" if upcoming else "None"

    user = f"""PATIENT: {snapshot['name']} | {snapshot['disease']}
Today: {snapshot['today']} | Check-ins: {snapshot['checkin_count']} | Days silent: {snapshot['days_silent']}
Risk: {snapshot['risk_level']} ({snapshot['risk_score']})
Dates: {snapshot['dates']}
Scores: {snapshot['scores']}
Statuses: {snapshot['statuses']}
Day-of-week avgs: {json.dumps(dow_summary)}
Missed med dates: {snapshot['missed_dates'] or 'None'}
Meds: {snapshot['med_schedule']}
Upcoming appt: {appt_str}
Already flagged: {snapshot['already_flagged']}"""

    try:
        resp = await llm.ainvoke([SystemMessage(content=system), HumanMessage(content=user)])
        text = _extract_content(resp).replace("```json", "").replace("```", "").strip()
        if not text:
            raise ValueError("Empty guardian response")
        return json.loads(text)
    except Exception:
        return {
            "findings": [],
            "overall_assessment": "Guardian completed analysis — no notable patterns detected.",
            "patient_message": "Your health data was reviewed. Everything looks stable.",
            "actions_taken_summary": "No actions triggered.",
        }


async def _act(db: AsyncSession, reasoning: dict, snapshot: dict) -> dict:
    action_log = []
    findings = reasoning.get("findings", [])

    appt_imminent = False
    upcoming = snapshot.get("upcoming")
    if upcoming:
        try:
            appt_date = datetime.strptime(upcoming["slot_date"], "%Y-%m-%d").date()
            appt_imminent = (appt_date - date.today()).days <= 2
        except ValueError:
            pass

    for finding in findings:
        action = finding.get("action", "none")
        severity = finding.get("severity", "low")

        if appt_imminent and action in ("alert_doctor", "flag_in_brief"):
            severity = "high"
            finding["severity"] = "high"
            finding["description"] = (finding.get("description", "") + " Escalated — appointment within 48h.").strip()

        if action == "alert_doctor" and severity in ("medium", "high", "severe"):
            msg = finding.get("alert_message") or finding.get("description") or finding.get("title", "Health concern")
            msg = (
                f"Health Guardian noticed: {finding.get('title', 'Pattern')}. "
                f"{msg}"
            )
            already = any(msg[:50] in f for f in snapshot.get("already_flagged", []))
            if not already:
                await create_clinical_alert(
                    db,
                    patient_id=snapshot["patient_id"],
                    doctor_id=snapshot.get("doctor_id"),
                    alert_type="Health Guardian — Pattern Detected",
                    message=msg,
                    severity=severity,
                )
                action_log.append({
                    "action": "alert_sent",
                    "finding": finding.get("title", ""),
                    "severity": severity,
                    "timestamp": datetime.now().isoformat(),
                    "escalated": appt_imminent,
                })
        elif action in ("flag_in_brief", "monitor"):
            action_log.append({
                "action": action,
                "finding": finding.get("title", ""),
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
            })

    await db.flush()
    return {
        "action_log": action_log,
        "alerts_sent": sum(1 for a in action_log if a.get("action") == "alert_sent"),
        "appointment_imminent": appt_imminent,
    }


async def _get_cached_today(db: AsyncSession, patient_id: str, workflow_type: str = "guardian_daily") -> dict | None:
    today = date.today()
    result = await db.execute(
        select(AgentRun)
        .where(
            AgentRun.patient_id == patient_id,
            AgentRun.workflow_type == workflow_type,
            AgentRun.status == "completed",
        )
        .order_by(AgentRun.started_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    if run and run.started_at.date() == today and run.result:
        return run.result
    return None


async def run_guardian(
    db: AsyncSession,
    patient_id: str,
    force: bool = False,
    workflow_type: str = "guardian_daily",
) -> dict:
    cached = None if force else await _get_cached_today(db, patient_id, workflow_type)
    if cached:
        return {**cached, "cached": True}

    result = await db.execute(
        select(Patient).where(Patient.id == patient_id).options(selectinload(Patient.doctor))
    )
    patient = result.scalar_one_or_none()
    if not patient:
        return {"error": "Patient not found"}

    run = AgentRun(patient_id=patient_id, workflow_type=workflow_type, status="running", events=[])
    db.add(run)
    await db.flush()

    ran_at = datetime.now().isoformat()
    try:
        snapshot = await _perceive(db, patient)
        reasoning = await _reason(snapshot)
        actions = await _act(db, reasoning, snapshot)

        from app.services.mcq_service import get_mcq_trends
        trends = await get_mcq_trends(db, patient_id, days=14)

        payload = {
            "snapshot": snapshot,
            "reasoning": reasoning,
            "actions": actions,
            "trends": trends,
            "ran_at": ran_at,
            "error": None,
            "cached": False,
            "source": workflow_type,
        }
        run.status = "completed"
        run.result = payload
        run.completed_at = datetime.now()
        await db.flush()
        return payload
    except Exception as exc:
        run.status = "failed"
        run.result = {"error": str(exc)}
        run.completed_at = datetime.now()
        await db.flush()
        return {
            "snapshot": {},
            "reasoning": {"findings": [], "overall_assessment": f"Guardian error: {exc}", "patient_message": "", "actions_taken_summary": ""},
            "actions": {"action_log": [], "alerts_sent": 0, "appointment_imminent": False},
            "trends": {"points": [], "summary": {}},
            "ran_at": ran_at,
            "error": str(exc),
            "cached": False,
        }
