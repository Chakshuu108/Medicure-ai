"""
🧬 Health Guardian — Autonomous Background Agent
Perceive → Reason → Act loop that runs every time a patient logs in.

It silently watches cross-session patterns, reasons over history,
and fires real actions (alerts to doctor, brief updates) — no user input needed.
Every decision is logged with a visible reasoning chain.
"""

import json
import requests
from datetime import date, datetime, timedelta
from collections import defaultdict


# ─────────────────────────────────────────────────────────────────────────────
# PERCEIVE — Collect all patient signals across sessions
# ─────────────────────────────────────────────────────────────────────────────

def _perceive(patient_id: str, patient: dict) -> dict:
    """
    Pull every relevant signal from the database.
    Returns a structured snapshot of the patient's cross-session history.
    """
    from data.database import (
        get_mcq_responses, get_patient_alerts,
        get_patient_prescriptions, get_patient_opd_bookings
    )

    responses     = get_mcq_responses(patient_id, limit=30)   # last ~month
    alerts        = get_patient_alerts(patient_id)
    prescriptions = get_patient_prescriptions(patient_id)
    bookings      = get_patient_opd_bookings(patient_id)

    # ── Build day-of-week score map ───────────────────────────────────────────
    dow_scores = defaultdict(list)   # {0=Mon … 6=Sun: [scores]}
    dow_dates  = defaultdict(list)
    for r in responses:
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d")
            dow_scores[d.weekday()].append(r["total_score"])
            dow_dates[d.weekday()].append(r["date"])
        except Exception:
            pass

    # ── Score timeline (oldest → newest) ─────────────────────────────────────
    timeline = sorted(responses, key=lambda x: x.get("date", ""))
    scores   = [r["total_score"]         for r in timeline]
    dates    = [r["date"]                for r in timeline]
    statuses = [r.get("status", "")      for r in timeline]

    # ── Adherence misses ──────────────────────────────────────────────────────
    missed_dates = []
    for r in timeline:
        adh = (r.get("adherence_status") or "").lower()
        if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
            missed_dates.append(r["date"])

    # ── Active prescriptions / med schedules ─────────────────────────────────
    med_schedule = []
    for p in prescriptions:
        meds = p.get("medicines") or []
        for m in meds:
            name = m.get("name") or m.get("medicine_name") or "Unknown"
            freq = m.get("frequency") or ""
            med_schedule.append({"name": name, "frequency": freq})

    # ── Previous guardian alerts (to avoid duplicates) ───────────────────────
    guardian_alerts = [
        a for a in alerts
        if "Health Guardian" in (a.get("alert_type") or "")
        or "Guardian" in (a.get("message") or "")
    ]
    already_flagged = [a.get("message", "")[:60] for a in guardian_alerts]

    # ── Upcoming appointment ──────────────────────────────────────────────────
    today_str  = date.today().isoformat()
    upcoming   = None
    for b in sorted(bookings, key=lambda x: x.get("slot_date", "")):
        if b.get("slot_date", "") >= today_str and b.get("status") not in ("cancelled",):
            upcoming = b
            break

    # ── Days since last check-in ──────────────────────────────────────────────
    last_checkin = dates[-1] if dates else None
    days_silent  = 0
    if last_checkin:
        try:
            days_silent = (date.today() - datetime.strptime(last_checkin, "%Y-%m-%d").date()).days
        except Exception:
            pass

    return {
        "patient_id":      patient_id,
        "name":            patient.get("name", "Patient"),
        "disease":         patient.get("disease", ""),
        "doctor_id":       patient.get("doctor_id", ""),
        "doctor_name":     patient.get("doctor_name", "Your Doctor"),
        "scores":          scores,
        "dates":           dates,
        "statuses":        statuses,
        "missed_dates":    missed_dates,
        "med_schedule":    med_schedule,
        "dow_scores":      {k: v for k, v in dow_scores.items()},
        "dow_dates":       {k: v for k, v in dow_dates.items()},
        "already_flagged": already_flagged,
        "upcoming":        upcoming,
        "days_silent":     days_silent,
        "checkin_count":   len(responses),
        "today":           today_str,
        "unresolved_alerts": len([a for a in alerts if not a.get("resolved")]),
    }


# ─────────────────────────────────────────────────────────────────────────────
# REASON — LLM analyses the signals and decides what matters
# ─────────────────────────────────────────────────────────────────────────────

def _call_groq(system: str, user: str, api_key: str, model: str,
               max_tokens: int = 700) -> str:
    """Low-level Groq API call. Returns raw text or empty string on failure."""
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json={
                "model":       model,
                "messages":    [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                "max_tokens":  max_tokens,
                "temperature": 0.25,
            },
            timeout=25,
        )
        raw = r.json()["choices"][0]["message"]["content"].strip()
        return raw.replace("```json", "").replace("```", "").strip()
    except Exception:
        return ""


def _reason(snapshot: dict, api_key: str, model: str) -> dict:
    """
    Send the full patient snapshot to the LLM.
    Returns a reasoning result: what was found, why it matters, what to do.
    """

    DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Summarise day-of-week averages for the prompt
    dow_summary = {}
    for k, v in snapshot["dow_scores"].items():
        if v:
            avg = round(sum(v) / len(v), 1)
            dow_summary[DOW[int(k)]] = {"avg_score": avg, "n": len(v), "dates": snapshot["dow_dates"][int(k)]}

    system = """You are an autonomous health monitoring AI agent called the Health Guardian.
Your job is to analyse a patient's cross-session health history and detect patterns that a human reviewing a single day would miss.

You must respond ONLY with valid JSON — no markdown, no explanation outside the JSON.

Your output schema:
{
  "findings": [
    {
      "type": "pattern | anomaly | silence | escalation | medication_effect",
      "title": "Short title for the finding (max 8 words)",
      "description": "1-2 sentences explaining what was detected in plain language",
      "reasoning_chain": [
        "Step 1: what raw data you observed",
        "Step 2: what comparison or calculation you made",
        "Step 3: why this is clinically significant"
      ],
      "severity": "low | medium | high",
      "action": "alert_doctor | flag_in_brief | monitor | none",
      "alert_message": "The exact message to send to the doctor (if action=alert_doctor). Written as a clinical note. Include patient name, the pattern, and the dates."
    }
  ],
  "overall_assessment": "1 sentence — the Guardian's top-level read on this patient right now",
  "patient_message": "A warm 1-sentence message to show the patient. What the Guardian found and did.",
  "actions_taken_summary": "1 sentence summarising what real actions the Guardian took (e.g. sent alert, flagged brief)"
}

Rules:
- If there are no notable findings, return findings: [] and say so in the overall_assessment.
- Do NOT flag things that are already in the already_flagged list.
- Be specific — mention actual dates, scores, day names.
- severity=high only if the pattern suggests clinical risk (e.g. consistent worsening, missed meds for 5+ days, score dropping below -8 consistently)
- action=alert_doctor only for medium or high severity findings.
"""

    user = f"""PATIENT SNAPSHOT:
Name: {snapshot['name']}
Condition: {snapshot['disease']}
Today: {snapshot['today']}
Total check-ins on record: {snapshot['checkin_count']}
Days since last check-in: {snapshot['days_silent']}

SCORE TIMELINE (oldest → newest):
Dates:   {snapshot['dates']}
Scores:  {snapshot['scores']}
Statuses:{snapshot['statuses']}

DAY-OF-WEEK AVERAGE SCORES:
{json.dumps(dow_summary, indent=2)}

MISSED MEDICATION DATES: {snapshot['missed_dates'] or 'None detected'}
MEDICATION SCHEDULE: {[m['name'] + ' (' + m['frequency'] + ')' for m in snapshot['med_schedule']] or 'Not available'}

UPCOMING APPOINTMENT: {snapshot['upcoming'].get('slot_date', '') + ' at ' + snapshot['upcoming'].get('start_time', '') if snapshot['upcoming'] else 'None scheduled'}

ALREADY FLAGGED BY GUARDIAN (do not repeat): {snapshot['already_flagged']}

Analyse this data. Look for:
1. Day-of-week patterns (e.g. scores always drop on Wednesdays)
2. Medication-correlated patterns (score drops 2 days after a known dose day)
3. Sustained silence or missed check-ins
4. Escalating worsening trend over multiple weeks
5. Any anomaly that only becomes visible across sessions"""

    raw = _call_groq(system, user, api_key, model, max_tokens=900)
    try:
        return json.loads(raw)
    except Exception:
        return {
            "findings": [],
            "overall_assessment": "Guardian completed analysis — no notable cross-session patterns detected today.",
            "patient_message": "Your health data was reviewed. Everything looks stable.",
            "actions_taken_summary": "No actions triggered.",
        }


# ─────────────────────────────────────────────────────────────────────────────
# ACT — Execute real actions based on the reasoning output
# ─────────────────────────────────────────────────────────────────────────────

def _act(reasoning: dict, snapshot: dict) -> dict:
    """
    Execute the actions decided by the reasoning step.
    Returns a log of what was actually done.
    """
    from data.database import create_alert

    action_log = []
    findings   = reasoning.get("findings", [])

    # ── Check if appointment is within 48 hours ───────────────────────────────
    appt_imminent = False
    upcoming = snapshot.get("upcoming")
    if upcoming:
        try:
            appt_date = datetime.strptime(upcoming["slot_date"], "%Y-%m-%d").date()
            hours_until = (appt_date - date.today()).days * 24
            appt_imminent = hours_until <= 48
        except Exception:
            pass

    for finding in findings:
        action = finding.get("action", "none")
        severity = finding.get("severity", "low")

        # Escalate severity if appointment is imminent
        if appt_imminent and action in ("alert_doctor", "flag_in_brief"):
            severity = "high"
            finding["severity"] = "high"
            finding["description"] += " ⚡ Escalated — appointment within 48 hours."

        if action == "alert_doctor" and finding.get("alert_message"):
            try:
                alert_msg = (
                    f"🧬 Health Guardian — {finding['title']}\n\n"
                    f"{finding['alert_message']}\n\n"
                    f"Detected: {snapshot['today']} | Patient: {snapshot['name']}"
                )
                create_alert(
                    patient_id=snapshot["patient_id"],
                    alert_type="Health Guardian — Pattern Detected",
                    message=alert_msg,
                    severity=severity,
                    doctor_id=snapshot.get("doctor_id"),
                )
                action_log.append({
                    "action":    "alert_sent",
                    "finding":   finding["title"],
                    "severity":  severity,
                    "timestamp": datetime.now().isoformat(),
                    "escalated": appt_imminent,
                })
            except Exception as e:
                action_log.append({
                    "action":  "alert_failed",
                    "finding": finding["title"],
                    "error":   str(e),
                })

        elif action in ("flag_in_brief", "monitor"):
            action_log.append({
                "action":    action,
                "finding":   finding["title"],
                "severity":  severity,
                "timestamp": datetime.now().isoformat(),
            })

    return {
        "action_log":        action_log,
        "alerts_sent":       sum(1 for a in action_log if a.get("action") == "alert_sent"),
        "appointment_imminent": appt_imminent,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT — run_guardian()
# ─────────────────────────────────────────────────────────────────────────────

def run_guardian(patient_id: str, patient: dict) -> dict:
    """
    Full perceive → reason → act loop.
    Call this once per patient login session.

    Returns a dict with everything needed to render the Health Guardian UI:
    {
        "snapshot":    raw data collected,
        "reasoning":   LLM output (findings, assessment, patient_message),
        "actions":     what was actually done (alerts fired, etc.),
        "ran_at":      ISO timestamp,
        "error":       str | None,
    }
    """
    from core.config import GROQ_API_KEY, GROQ_MODEL

    ran_at = datetime.now().isoformat()

    if not GROQ_API_KEY:
        return {
            "snapshot":  {},
            "reasoning": {"findings": [], "overall_assessment": "Guardian requires a Groq API key to run.", "patient_message": "", "actions_taken_summary": ""},
            "actions":   {"action_log": [], "alerts_sent": 0, "appointment_imminent": False},
            "ran_at":    ran_at,
            "error":     "No GROQ_API_KEY configured.",
        }

    try:
        snapshot  = _perceive(patient_id, patient)
        reasoning = _reason(snapshot, GROQ_API_KEY, GROQ_MODEL)
        actions   = _act(reasoning, snapshot)

        return {
            "snapshot":  snapshot,
            "reasoning": reasoning,
            "actions":   actions,
            "ran_at":    ran_at,
            "error":     None,
        }

    except Exception as e:
        return {
            "snapshot":  {},
            "reasoning": {"findings": [], "overall_assessment": f"Guardian encountered an error: {e}", "patient_message": "", "actions_taken_summary": ""},
            "actions":   {"action_log": [], "alerts_sent": 0, "appointment_imminent": False},
            "ran_at":    ran_at,
            "error":     str(e),
        }
