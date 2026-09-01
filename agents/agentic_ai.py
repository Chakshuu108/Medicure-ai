"""
agentic_ai.py — Fully Autonomous Agentic AI System for MediCure
================================================================

Decision engine that:
  1. Classifies intent from free-form natural language
  2. Extracts required slots (doctor, date, time, symptoms, …)
  3. MERGES slots across conversation turns — partial info accumulates
  4. Executes tasks autonomously when all slots are present
  5. Asks for ONLY the first missing slot when info is incomplete
  6. Sends email confirmations for bookings
  7. Handles multi-turn booking flows, cancellations, health Q&A,
     medication safety, symptom triage, prescription views, alerts

Architecture
------------
  AgenticAI.process()
    ├─ _build_patient_context()      patient profile + medications
    ├─ classify_intent_and_slots()   LLM → intent + slot values
    ├─ _merge_slots()                accumulate info across turns
    ├─ execute_*()                   action executors
    └─ _handle_general_or_medical()  LLM handler for health Q&A
"""

import json
import re
import requests
from datetime import datetime, date, timedelta

from data.database import (
    get_patient, get_patient_prescriptions, get_chat_history,
    save_chat_message, get_patient_alerts, get_patient_opd_bookings,
    get_available_opd_doctors, get_available_opd_dates_for_doctor,
    get_available_opd_slots, book_opd_slot, cancel_opd_booking,
    check_patient_has_booking, create_alert, get_hospital,
)
from core.config import GROQ_API_KEY, GROQ_MODEL, MAX_CHAT_HISTORY

try:
    from core.email_service import send_registration_email, send_action_email
    _EMAIL_AVAILABLE = True
except ImportError:
    _EMAIL_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────
# SAFETY / TRIAGE PROMPT FRAGMENTS
# ─────────────────────────────────────────────────────────────────────────────

SAFETY_RULES = """
MEDICAL SAFETY VALIDATION — MANDATORY ON EVERY MEDICATION RESPONSE
You are NOT a rubber-stamp assistant. Always reason from first principles.
Check: (1) condition–drug match, (2) dosage range, (3) drug–drug interactions,
(4) patient-specific risks (age, gender, risk score).
Flag ⚠️ MISMATCH / ⚠️ DOSAGE CONCERN / ⚠️ INTERACTION RISK / ⚠️ UNUSUAL for any concern.
Never say "your prescription looks correct" without explicit clinical reasoning.
Always end with: "This is informational only. Always follow your doctor's guidance."
"""

SYMPTOM_RULES = """
SYMPTOM CHECKER MODE — ACTIVATED
If symptom description is vague, ask ONE focused follow-up question max before triaging.
Analyse symptoms against the patient's age, gender, condition, risk score, and medications.
Always end your response with EXACTLY one of:
  TRIAGE_VERDICT: URGENT
  TRIAGE_VERDICT: MODERATE
  TRIAGE_VERDICT: MILD
"""

# ─────────────────────────────────────────────────────────────────────────────
# INTENT + SLOT DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────

INTENTS = {
    "book_appointment":    {"slots": ["doctor", "date", "time"]},
    "cancel_appointment":  {"slots": ["appointment_id_or_doctor"]},
    "view_appointments":   {"slots": []},
    "view_prescriptions":  {"slots": []},
    "check_symptoms":      {"slots": ["symptoms"]},
    "medication_query":    {"slots": ["medication_name"]},
    "view_alerts":         {"slots": []},
    "general_health":      {"slots": []},
}

# What to ask when a slot is missing — concise, one question at a time
_SLOT_QUESTIONS = {
    "doctor": "Which doctor would you like to see?",
    "date":   "On which date would you like the appointment? (e.g. tomorrow, 20 April)",
    "time":   "What time would you prefer?",
    "appointment_id_or_doctor": "Which appointment would you like to cancel? Please tell me the doctor's name.",
    "symptoms":       "Please describe your symptoms in as much detail as you can.",
    "medication_name":"Which medication would you like to ask about?",
}

# ─────────────────────────────────────────────────────────────────────────────
# GROQ LLM HELPER
# ─────────────────────────────────────────────────────────────────────────────

def _groq(messages: list, max_tokens: int = 900, temperature: float = 0.2) -> str | None:
    if not GROQ_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={"model": GROQ_MODEL, "messages": messages,
                  "max_tokens": max_tokens, "temperature": temperature},
            timeout=30,
        )
        r.raise_for_status()
        choices = r.json().get("choices", [])
        return choices[0]["message"]["content"] if choices else None
    except Exception:
        return None


def _extract_triage(text: str) -> str | None:
    for line in text.splitlines():
        if line.strip().startswith("TRIAGE_VERDICT:"):
            v = line.split(":", 1)[1].strip().upper()
            if v in ("URGENT", "MODERATE", "MILD"):
                return v
    return None


def _strip_triage(text: str) -> str:
    return "\n".join(
        l for l in text.splitlines() if not l.strip().startswith("TRIAGE_VERDICT:")
    ).strip()

# ─────────────────────────────────────────────────────────────────────────────
# DATE NORMALISER
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_date(raw: str) -> str:
    """Convert free-text date to YYYY-MM-DD.  Returns raw string on failure."""
    if not raw:
        return ""
    s = raw.strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        return s
    today = date.today()
    low = s.lower()
    if low == "today":
        return today.isoformat()
    if low == "tomorrow":
        return (today + timedelta(days=1)).isoformat()
    if "day after" in low:
        return (today + timedelta(days=2)).isoformat()
    # Try with year first, then without
    for fmt in ("%d %B %Y", "%d %b %Y", "%B %d %Y", "%b %d %Y",
                "%d/%m/%Y", "%d-%m-%Y", "%d %B", "%d %b"):
        try:
            parsed = datetime.strptime(s, fmt)
            if parsed.year == 1900:
                parsed = parsed.replace(year=today.year)
                if parsed.date() < today:
                    parsed = parsed.replace(year=today.year + 1)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s  # return original if we can't parse

# ─────────────────────────────────────────────────────────────────────────────
# INTENT + SLOT CLASSIFICATION  (LLM-powered)
# ─────────────────────────────────────────────────────────────────────────────

def classify_intent_and_slots(
    user_message: str,
    patient_context: str,
    conversation_history: list,
) -> dict:
    """
    Returns:
      { intent, slots{}, confidence, missing_slots[], raw_intent_description }
    """
    history_text = "\n".join(
        f"{h['role'].upper()}: {h['content'][:200]}"
        for h in conversation_history[-8:]
    )

    system = f"""You are an intent + slot extractor for a healthcare management system.
Output ONLY valid JSON — no markdown, no explanation.

{patient_context}

Recent conversation (last 8 turns):
{history_text}

INTENTS:
  book_appointment   — needs: doctor, date, time
  cancel_appointment — needs: appointment_id_or_doctor
  view_appointments  — needs nothing
  view_prescriptions — needs nothing
  check_symptoms     — needs: symptoms (free-text description)
  medication_query   — needs: medication_name
  view_alerts        — needs nothing
  general_health     — needs nothing (catch-all for health chat)

SLOT RULES:
  doctor       : any doctor name, partial or full (include "Dr." prefix if given)
  date         : any date reference — keep as text if you can't parse it
  time         : any time reference (morning, 10am, afternoon, etc.)
  symptoms     : full symptom description verbatim
  medication_name : medication/drug name mentioned
  appointment_id_or_doctor : doctor name or slot reference for cancellation

JSON SCHEMA (fill nulls for absent slots):
{{
  "intent": "<name>",
  "slots": {{
    "doctor": "<value or null>",
    "date": "<value or null>",
    "time": "<value or null>",
    "symptoms": "<value or null>",
    "medication_name": "<value or null>",
    "appointment_id_or_doctor": "<value or null>"
  }},
  "confidence": 0.95,
  "raw_intent_description": "one-sentence description"
}}"""

    resp = _groq(
        [{"role": "system", "content": system},
         {"role": "user",   "content": user_message}],
        max_tokens=350, temperature=0.05,
    )

    if not resp:
        return {"intent": "general_health", "slots": {}, "confidence": 0.4,
                "missing_slots": [], "raw_intent_description": user_message}

    try:
        clean = resp.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        data = json.loads(clean)
        intent = data.get("intent", "general_health")
        slots  = data.get("slots", {})
        required = INTENTS.get(intent, {}).get("slots", [])
        missing  = [s for s in required if not slots.get(s)]
        return {
            "intent": intent,
            "slots": slots,
            "confidence": data.get("confidence", 0.8),
            "missing_slots": missing,
            "raw_intent_description": data.get("raw_intent_description", ""),
        }
    except Exception:
        return {"intent": "general_health", "slots": {}, "confidence": 0.4,
                "missing_slots": [], "raw_intent_description": user_message}

# ─────────────────────────────────────────────────────────────────────────────
# ACTION EXECUTORS
# ─────────────────────────────────────────────────────────────────────────────

def _fuzzy_match_doctor(query: str, doctors: list) -> dict | None:
    """Find best doctor match from available list."""
    if not query:
        return None
    q = query.lower().replace("dr.", "").replace("dr ", "").strip()
    # Exact substring match
    for d in doctors:
        if q in d["name"].lower() or d["name"].lower() in q:
            return d
    # Word-level match
    q_words = set(w for w in q.split() if len(w) > 2)
    best, best_score = None, 0
    for d in doctors:
        name_words = set(d["name"].lower().split())
        score = len(q_words & name_words)
        if score > best_score:
            best, best_score = d, score
    return best if best_score > 0 else None


def _fuzzy_match_time(query: str, free_slots: list) -> dict | None:
    """Match a time preference to an available slot."""
    if not query or not free_slots:
        return None
    q = query.lower().strip()

    # Direct time match (e.g. "10:30", "10 am")
    time_clean = re.sub(r"[^0-9:]", "", q)
    if time_clean:
        for s in free_slots:
            if s["start_time"].replace(":", "").startswith(time_clean.replace(":", "")):
                return s

    # Period keywords
    if any(k in q for k in ["morning", "am", "early"]):
        return next((s for s in free_slots if s["start_time"] < "12:00"), free_slots[0])
    if any(k in q for k in ["afternoon", "noon", "lunch"]):
        return next((s for s in free_slots if "12:00" <= s["start_time"] < "17:00"), None) or free_slots[0]
    if any(k in q for k in ["evening", "pm", "late"]):
        return next((s for s in free_slots if s["start_time"] >= "17:00"), None) or free_slots[-1]

    return free_slots[0]  # default to first


def execute_book_appointment(patient_id: str, slots: dict, patient: dict) -> dict:
    """Book an OPD slot. Returns full result dict."""
    all_doctors = get_available_opd_doctors()
    if not all_doctors:
        return {"success": False, "action": "book_appointment",
                "message": "No doctors currently have available OPD slots. Please try again later."}

    # ── Match doctor ──────────────────────────────────────────────────────────
    doctor_q = (slots.get("doctor") or "").strip()
    matched_doctor = _fuzzy_match_doctor(doctor_q, all_doctors)

    if not matched_doctor:
        doc_list = "\n".join(
            f"• Dr. {d['name']} — {d.get('specialization', 'General')}" for d in all_doctors
        )
        return {
            "success": False, "action": "book_appointment",
            "message": (
                f"I couldn't find **{doctor_q}** in the available doctors.\n\n"
                f"**Available doctors:**\n{doc_list}\n\n"
                "Please tell me which doctor you'd like to see."
            ),
            "show_doctors": all_doctors,
        }

    # ── Match date ────────────────────────────────────────────────────────────
    date_q   = (slots.get("date") or "").strip()
    date_str = _normalise_date(date_q)
    available_dates = get_available_opd_dates_for_doctor(matched_doctor["doctor_id"])

    if not available_dates:
        return {
            "success": False, "action": "book_appointment",
            "message": f"Dr. {matched_doctor['name']} has no available dates right now. Try another doctor.",
        }

    matched_date = date_str if date_str in available_dates else None
    if not matched_date:
        date_list = "\n".join(
            f"• {datetime.strptime(d, '%Y-%m-%d').strftime('%A, %d %b %Y')}" for d in available_dates[:6]
        )
        return {
            "success": False, "action": "book_appointment",
            "message": (
                (f"**{date_q}** is not available. " if date_q else "")
                + f"Dr. {matched_doctor['name']} has slots on:\n\n{date_list}\n\nWhich date would you like?"
            ),
            "available_dates": available_dates,
            "doctor": matched_doctor,
        }

    # ── Check duplicate booking ───────────────────────────────────────────────
    if check_patient_has_booking(patient_id, matched_doctor["doctor_id"], matched_date):
        return {
            "success": False, "action": "book_appointment",
            "message": (
                f"You already have an appointment with Dr. {matched_doctor['name']} "
                f"on {matched_date}. Check **My Appointments** to view or cancel it."
            ),
        }

    # ── Match time ────────────────────────────────────────────────────────────
    all_slots  = get_available_opd_slots(matched_doctor["doctor_id"], matched_date)
    free_slots = [s for s in all_slots if not s.get("is_booked")]

    if not free_slots:
        return {
            "success": False, "action": "book_appointment",
            "message": f"All slots for Dr. {matched_doctor['name']} on {matched_date} are booked. Choose another date.",
        }

    time_q       = (slots.get("time") or "").strip()
    matched_slot = _fuzzy_match_time(time_q, free_slots)

    if not matched_slot and len(free_slots) > 1:
        slot_list = "\n".join(f"• {s['start_time']} – {s['end_time']}" for s in free_slots[:8])
        return {
            "success": False, "action": "book_appointment",
            "message": (
                (f"**{time_q}** is not available. " if time_q else "")
                + f"Available times for Dr. {matched_doctor['name']} on {matched_date}:\n\n{slot_list}\n\nWhich time would you like?"
            ),
            "available_slots": free_slots, "doctor": matched_doctor, "date": matched_date,
        }

    # If only one slot or matched — auto-book
    if not matched_slot:
        matched_slot = free_slots[0]

    # ── BOOK ──────────────────────────────────────────────────────────────────
    booked = book_opd_slot(matched_slot["id"], patient_id, patient.get("name", ""))
    if not booked:
        return {
            "success": False, "action": "book_appointment",
            "message": "That slot was just taken. Please choose another time.",
        }

    date_fmt = datetime.strptime(matched_date, "%Y-%m-%d").strftime("%A, %d %B %Y")
    confirm_msg = (
        f"✅ **Appointment Confirmed!**\n\n"
        f"| | |\n|---|---|\n"
        f"| **Doctor** | Dr. {matched_doctor['name']} |\n"
        f"| **Specialization** | {matched_doctor.get('specialization', 'General')} |\n"
        f"| **Date** | {date_fmt} |\n"
        f"| **Time** | {matched_slot['start_time']} – {matched_slot['end_time']} |\n"
        f"| **Patient** | {patient.get('name', '')} |\n\n"
        f"Please arrive 10 minutes before your slot. "
        f"You can join your video call from the **Online OPD** tab."
    )

    # ── Try to send booking confirmation email ────────────────────────────────
    email_status = ""
    patient_email = patient.get("email", "")
    if _EMAIL_AVAILABLE and patient_email:
        try:
            hospital_id  = patient.get("hospital_id", "")
            hospital     = get_hospital(hospital_id) or {}
            email_data = {
                "patient_id":       patient_id,
                "name":             patient.get("name", ""),
                "age":              patient.get("age", ""),
                "gender":           patient.get("gender", ""),
                "contact":          patient.get("contact", ""),
                "email":            patient_email,
                "disease":          patient.get("disease", ""),
                "visit_date":       matched_date,
                "doctor_name":      matched_doctor["name"],
                "doctor_dept":      matched_doctor.get("specialization", "General"),
                "hospital_name":    hospital.get("name", "MediCure"),
                "hospital_address": hospital.get("address", ""),
                "hospital_city":    hospital.get("city", ""),
                "hospital_pincode": hospital.get("pincode", ""),
                "hospital_phone":   hospital.get("phone", ""),
                "hospital_email":   hospital.get("email", ""),
                "hospital_website": hospital.get("website", ""),
                "token_number":     matched_slot.get("id", "")[-6:].upper(),
                "consultation_type": f"OPD Online — {matched_slot['start_time']}",
            }
            ok, msg = send_registration_email(email_data)
            email_status = f"\n\n📧 Confirmation email sent to **{patient_email}**." if ok else ""
        except Exception:
            email_status = ""

    return {
        "success": True, "action": "book_appointment", "confirmed": True,
        "message": confirm_msg + email_status,
        "booking_details": {
            "doctor":         matched_doctor["name"],
            "specialization": matched_doctor.get("specialization", ""),
            "date":           matched_date,
            "date_fmt":       date_fmt,
            "time":           f"{matched_slot['start_time']} – {matched_slot['end_time']}",
            "slot_id":        matched_slot["id"],
        },
    }


def execute_cancel_appointment(patient_id: str, slots: dict, patient: dict) -> dict:
    bookings = get_patient_opd_bookings(patient_id)
    active   = [b for b in bookings if b.get("is_booked") and not b.get("visited")]

    if not active:
        return {"success": False, "action": "cancel_appointment",
                "message": "You have no upcoming appointments to cancel."}

    query = (slots.get("appointment_id_or_doctor") or "").lower().replace("dr.", "").replace("dr ", "").strip()
    matched = None

    if query:
        for b in active:
            if query in b.get("doctor_name", "").lower():
                matched = b
                break

    if not matched and len(active) == 1:
        matched = active[0]

    if not matched:
        blist = "\n".join(
            f"• Dr. {b.get('doctor_name', '?')} — "
            f"{datetime.strptime(b['slot_date'], '%Y-%m-%d').strftime('%d %b %Y')} "
            f"at {b.get('start_time', '')}"
            for b in active
        )
        return {
            "success": False, "action": "cancel_appointment",
            "message": f"Which appointment would you like to cancel?\n\n{blist}\n\nPlease tell me the doctor's name.",
            "active_bookings": active,
        }

    cancelled = cancel_opd_booking(matched["id"], patient_id)
    if cancelled:
        date_fmt = datetime.strptime(matched["slot_date"], "%Y-%m-%d").strftime("%A, %d %B %Y")

        # ── Send cancellation email ───────────────────────────────────────────
        if _EMAIL_AVAILABLE and patient.get("email"):
            try:
                send_action_email(
                    action_type   = "cancellation",
                    patient_name  = patient.get("name", "Patient"),
                    patient_email = patient["email"],
                    subject       = f"Appointment Cancelled — Dr. {matched.get('doctor_name','')} | {matched['slot_date']}",
                    headline      = "Your appointment has been cancelled",
                    body_html     = (
                        "Your appointment listed below has been successfully cancelled. "
                        "The slot has been released. If you would like to rebook, "
                        "please use the <strong>Online OPD</strong> tab or ask the AI Assistant."
                    ),
                    details_rows  = [
                        ("Doctor",      f"Dr. {matched.get('doctor_name', '')}"),
                        ("Date",        date_fmt),
                        ("Time",        matched.get("start_time", "")),
                        ("Patient ID",  patient_id),
                        ("Status",      "❌ Cancelled"),
                    ],
                    footer_note   = "If you did not request this cancellation, please contact reception immediately.",
                )
            except Exception:
                pass

        return {
            "success": True, "action": "cancel_appointment", "confirmed": True,
            "message": (
                f"✅ **Appointment Cancelled**\n\n"
                f"Your appointment with **Dr. {matched.get('doctor_name', '')}** "
                f"on **{date_fmt}** at **{matched.get('start_time', '')}** "
                f"has been cancelled. The slot is now available for others."
            ),
        }
    return {"success": False, "action": "cancel_appointment",
            "message": "Could not cancel — please contact reception."}


def execute_view_appointments(patient_id: str) -> dict:
    bookings = get_patient_opd_bookings(patient_id)
    active   = [b for b in bookings if b.get("is_booked") and not b.get("visited")]

    if not active:
        return {
            "success": True, "action": "view_appointments", "bookings": [],
            "message": "You have no upcoming appointments. Would you like to book one? Just say the word!",
        }

    lines = ["📅 **Your Upcoming Appointments**\n"]
    for b in active:
        date_fmt = datetime.strptime(b["slot_date"], "%Y-%m-%d").strftime("%A, %d %b %Y")
        lines.append(
            f"**Dr. {b.get('doctor_name', '?')}** · {b.get('specialization', '')}\n"
            f"  📆 {date_fmt} · ⏰ {b.get('start_time', '')} – {b.get('end_time', '')}"
        )
    return {"success": True, "action": "view_appointments", "bookings": active,
            "message": "\n\n".join(lines)}


def execute_view_prescriptions(patient_id: str) -> dict:
    prescriptions = get_patient_prescriptions(patient_id)
    if not prescriptions:
        return {"success": True, "action": "view_prescriptions",
                "message": "No prescriptions on record yet. Please consult your doctor."}

    lines = ["💊 **Your Current Prescriptions**\n"]
    for pr in prescriptions[:3]:
        pr_date = pr.get("created_at", "")[:10]
        lines.append(f"**Prescription — {pr_date}**")
        if pr.get("doctor_notes"):
            lines.append(f"> *Doctor's notes: {pr['doctor_notes']}*")
        for m in pr.get("medicines", []):
            lines.append(
                f"• **{m['name']}** — {m['dosage']} · {m['timing']} · {m['duration_days']} days"
            )
        lines.append("")
    return {"success": True, "action": "view_prescriptions",
            "message": "\n".join(lines), "prescriptions": prescriptions}


def execute_view_alerts(patient_id: str) -> dict:
    alerts    = get_patient_alerts(patient_id, resolved=False)
    if not alerts:
        return {"success": True, "action": "view_alerts", "alerts": [],
                "message": "✅ No active health alerts — you're all clear!"}

    icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    lines = [f"🔔 **You have {len(alerts)} active alert(s)**\n"]
    for a in alerts:
        icon = icons.get(a.get("severity", "low"), "🔔")
        lines.append(f"{icon} **{a.get('alert_type','Alert').replace('_',' ').title()}**\n  {a.get('message','')[:120]}")
    return {"success": True, "action": "view_alerts", "alerts": alerts,
            "message": "\n\n".join(lines)}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN AGENTIC AI CLASS
# ─────────────────────────────────────────────────────────────────────────────

class AgenticAI:
    """
    Autonomous medical AI agent.

    Slot memory:  partial slots accumulate in session across turns so that
                  multi-turn booking flows work naturally.
                  e.g. Turn1: "book with Dr. Sharma" → stores doctor
                       Turn2: "on 20 April"           → adds date
                       Turn3: "10am"                  → adds time → books!
    """

    # ── Public API ─────────────────────────────────────────────────────────

    def process(self, patient_id: str, user_message: str,
                session_state: dict | None = None) -> dict:
        """
        Main entry point.  `session_state` is passed in from Streamlit so that
        slot memory persists across reruns.

        Returns:
          { reply, triage, action, success, confirmed, booking_details?, needs_clarification }
        """
        save_chat_message(patient_id, "user", user_message)

        if not GROQ_API_KEY:
            reply = ("⚠️ AI service not configured. "
                     "Please add GROQ_API_KEY to your Streamlit secrets.")
            save_chat_message(patient_id, "assistant", reply)
            return {"reply": reply, "triage": None, "action": "none",
                    "needs_clarification": False, "success": False}

        patient_context, patient = self._build_context(patient_id)
        history = get_chat_history(patient_id, MAX_CHAT_HISTORY)

        # ── Classify intent + extract fresh slots ─────────────────────────
        classification = classify_intent_and_slots(user_message, patient_context, history)
        intent         = classification["intent"]
        fresh_slots    = classification.get("slots", {})

        # ── Merge with remembered slots (session) ─────────────────────────
        remembered = {}
        if session_state is not None:
            mem_key   = f"agent_slots_{patient_id}"
            intent_key= f"agent_intent_{patient_id}"
            remembered = session_state.get(mem_key, {})

            # If intent changed, clear memory (user started a new request)
            prev_intent = session_state.get(intent_key, intent)
            if prev_intent != intent and intent not in ("general_health", "check_symptoms",
                                                          "medication_query"):
                remembered = {}

            session_state[intent_key] = intent

        merged = self._merge_slots(remembered, fresh_slots)

        if session_state is not None:
            session_state[mem_key] = merged

        required = INTENTS.get(intent, {}).get("slots", [])
        missing  = [s for s in required if not merged.get(s)]

        # ── Zero-slot intents — execute immediately ───────────────────────
        if intent == "view_appointments":
            result = execute_view_appointments(patient_id)
            return self._finish(patient_id, result, session_state, patient_id)

        if intent == "view_prescriptions":
            result = execute_view_prescriptions(patient_id)
            return self._finish(patient_id, result, session_state, patient_id)

        if intent == "view_alerts":
            result = execute_view_alerts(patient_id)
            return self._finish(patient_id, result, session_state, patient_id)

        # ── Book appointment ──────────────────────────────────────────────
        if intent == "book_appointment":
            if missing:
                first_miss = missing[0]
                question   = _SLOT_QUESTIONS.get(first_miss, f"Please provide: {first_miss}")
                if first_miss == "doctor":
                    doctors = get_available_opd_doctors()
                    if doctors:
                        doc_list = "\n".join(
                            f"• **Dr. {d['name']}** — {d.get('specialization','General')}"
                            for d in doctors
                        )
                        question = f"Which doctor would you like to see?\n\n{doc_list}"
                save_chat_message(patient_id, "assistant", question)
                return {"reply": question, "triage": None, "action": "book_appointment",
                        "needs_clarification": True, "missing_slot": first_miss, "success": False}

            result = execute_book_appointment(patient_id, merged, patient)
            if result["success"] and session_state is not None:
                session_state.pop(f"agent_slots_{patient_id}", None)
                session_state.pop(f"agent_intent_{patient_id}", None)
            return self._finish(patient_id, result, session_state, patient_id)

        # ── Cancel appointment ────────────────────────────────────────────
        if intent == "cancel_appointment":
            result = execute_cancel_appointment(patient_id, merged, patient)
            if result["success"] and session_state is not None:
                session_state.pop(f"agent_slots_{patient_id}", None)
            return self._finish(patient_id, result, session_state, patient_id)

        # ── Medical / health Q&A — LLM handles ───────────────────────────
        result = self._llm_health(patient_id, user_message, intent, patient_context, patient, history)
        return self._finish(patient_id, result, session_state, patient_id)

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _merge_slots(remembered: dict, fresh: dict) -> dict:
        """Non-null fresh values override remembered; remembered fills gaps."""
        merged = dict(remembered)
        for k, v in fresh.items():
            if v:
                merged[k] = v
        return merged

    @staticmethod
    def _build_context(patient_id: str) -> tuple[str, dict]:
        from data.database import (
            get_mcq_responses, get_patient_opd_bookings,
            get_patient_alerts,
        )

        patient = get_patient(patient_id)
        if not patient:
            return "Patient profile unavailable.", {}

        today_str = date.today().isoformat()

        # ── Medications ───────────────────────────────────────────────────────
        prescriptions = get_patient_prescriptions(patient_id)
        meds = []
        for pr in prescriptions:
            for m in pr.get("medicines", []):
                meds.append(f"{m['name']} {m['dosage']} ({m['timing']})")

        # ── Recent check-in history (last 5) ─────────────────────────────────
        mcq_rows  = get_mcq_responses(patient_id, limit=7)
        statuses  = [r["status"]       for r in mcq_rows[:5]]
        scores    = [r["total_score"]  for r in mcq_rows[:5]]

        # Trend direction
        if len(scores) >= 4:
            half      = len(scores) // 2
            first_h   = sum(scores[:half]) / half
            second_h  = sum(scores[half:]) / (len(scores) - half)
            trend = ("improving" if second_h > first_h
                     else "worsening" if second_h < first_h
                     else "stable")
        elif scores:
            trend = statuses[0].lower() if statuses else "stable"
        else:
            trend = "no data yet"

        # Adherence flags
        missed_dates = []
        for r in mcq_rows:
            adh = (r.get("adherence_status") or "").lower()
            if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
                missed_dates.append(r["date"])

        # Reported symptoms from MCQs
        symptoms = []
        for r in mcq_rows[:5]:
            try:
                import json as _json
                resp_data = _json.loads(r.get("responses_json") or "{}")
                for q_data in resp_data.values():
                    if isinstance(q_data, dict):
                        sym = q_data.get("symptoms") or q_data.get("answer") or ""
                        if sym and isinstance(sym, str) and len(sym) > 3:
                            symptoms.append(sym)
            except Exception:
                pass

        # Side effects
        side_effects = []
        for r in mcq_rows[:5]:
            try:
                import json as _json
                se = _json.loads(r.get("side_effects") or "[]")
                if isinstance(se, list):
                    side_effects.extend(se)
            except Exception:
                pass

        # ── Upcoming appointment ──────────────────────────────────────────────
        bookings = get_patient_opd_bookings(patient_id)
        upcoming_appt = None
        for b in sorted(bookings, key=lambda x: x.get("slot_date", "")):
            if b.get("slot_date", "") >= today_str and b.get("status") not in ("cancelled",):
                upcoming_appt = (
                    f"Dr. {b.get('doctor_name', b.get('doctor_id', '?'))} "
                    f"on {b['slot_date']} at {b.get('start_time', '?')}"
                )
                break

        # ── Active alerts ─────────────────────────────────────────────────────
        all_alerts    = get_patient_alerts(patient_id)
        unresolved    = [a for a in all_alerts if not a.get("resolved")]
        high_alerts   = [a for a in unresolved if a.get("severity") == "high"]
        alert_summary = (
            f"{len(unresolved)} unresolved "
            f"({len(high_alerts)} high-priority)"
            if unresolved else "None"
        )

        # ── Doctor name ───────────────────────────────────────────────────────
        doctor_name = patient.get("doctor_name") or patient.get("doctor_id") or "not assigned"

        # ── Build context string ──────────────────────────────────────────────
        ctx_lines = [
            f"PATIENT: {patient['name']} | Age: {patient['age']} | Gender: {patient['gender']}",
            f"CONDITION: {patient['disease']}",
            f"ASSIGNED DOCTOR: Dr. {doctor_name}",
            f"RISK: {patient.get('risk_level', 'low').upper()} (Score: {patient.get('risk_score', 0)}/100)",
            f"HEALTH TREND (last {len(scores)} check-ins): {trend.upper()}",
            f"RECENT CHECK-IN STATUSES: {', '.join(statuses) if statuses else 'No check-ins yet'}",
            f"RECENT SCORES: {', '.join(str(s) for s in scores) if scores else 'N/A'}",
            f"MEDICATIONS: {'; '.join(meds) if meds else 'None prescribed'}",
            f"MEDICATION ADHERENCE: {'Missed doses on: ' + ', '.join(missed_dates[:3]) if missed_dates else 'Good — no missed doses detected'}",
            f"REPORTED SYMPTOMS (recent): {'; '.join(list(set(symptoms))[:5]) if symptoms else 'None reported'}",
            f"SIDE EFFECTS REPORTED: {'; '.join(list(set(side_effects))[:4]) if side_effects else 'None'}",
            f"UPCOMING APPOINTMENT: {upcoming_appt or 'None scheduled'}",
            f"ACTIVE ALERTS: {alert_summary}",
            f"TODAY: {today_str}",
        ]
        ctx = "\n".join(ctx_lines)
        return ctx, patient

    @staticmethod
    def _llm_health(patient_id, user_message, intent, patient_context, patient, history) -> dict:
        is_symptom = intent == "check_symptoms"
        is_med     = intent == "medication_query"

        system = f"""You are an autonomous AI healthcare assistant for {patient.get('name','the patient')}.
You are empathetic, precise, and action-oriented.

{patient_context}

ACTIONS YOU CAN INITIATE:
Tell the user you can book appointments, cancel bookings, show prescriptions,
check alerts, check symptoms, or answer health questions — and offer to do so.

{SAFETY_RULES if is_med else ''}
{SYMPTOM_RULES if is_symptom else ''}"""

        messages = [{"role": "system", "content": system}]
        for h in history[-MAX_CHAT_HISTORY:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        response = _groq(messages, max_tokens=1100, temperature=0.3)
        if not response:
            response = "I'm having trouble connecting right now. Please try again shortly."

        triage = None
        if is_symptom:
            triage   = _extract_triage(response)
            response = _strip_triage(response)

        return {"reply": response, "triage": triage, "action": intent,
                "success": True, "needs_clarification": False}

    @staticmethod
    def _finish(patient_id: str, result: dict,
                session_state: dict | None, _pid: str) -> dict:
        reply = result.get("reply") or result.get("message", "")
        save_chat_message(patient_id, "assistant", reply)
        return {
            "reply":              reply,
            "triage":             result.get("triage"),
            "action":             result.get("action", ""),
            "success":            result.get("success", True),
            "confirmed":          result.get("confirmed", False),
            "needs_clarification":result.get("needs_clarification", not result.get("success", True)),
            "booking_details":    result.get("booking_details"),
            "active_bookings":    result.get("active_bookings"),
            "show_doctors":       result.get("show_doctors"),
        }
