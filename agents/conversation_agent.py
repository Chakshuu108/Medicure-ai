import requests
import json
from data.database import (
    get_chat_history, save_chat_message, get_patient,
    get_patient_prescriptions, get_patients_by_doctor
)
from core.config import GROQ_API_KEY, GROQ_MODEL, MAX_CHAT_HISTORY


def _safe_extract_text(data: dict) -> str | None:
    """Safely extract text content from a GROQ/OpenAI API response dict."""
    choices = data.get("choices")
    if choices and isinstance(choices, list):
        msg = choices[0].get("message") or {}
        return msg.get("content")
    if data.get("error"):
        return None
    return None


# ---------------------------------------------------------------------------
# MEDICAL SAFETY KNOWLEDGE BASE
# ---------------------------------------------------------------------------

SAFETY_RULES = """
══════════════════════════════════════════════════════════════════════════════
MEDICAL SAFETY VALIDATION FRAMEWORK  (MANDATORY — APPLY TO EVERY RESPONSE)
══════════════════════════════════════════════════════════════════════════════

You are NOT a rubber-stamp assistant. Your primary duty is patient safety.
NEVER blindly confirm a prescription is correct just because it exists in the
system. Always reason from first principles.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A. CONDITION–DRUG MISMATCH DETECTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cross-check every prescribed medicine against the patient's primary condition.
Flag (⚠️ MISMATCH) if the drug class does not match the disease category.

Examples to detect:
  • Antibiotics prescribed for viral infections or non-infectious conditions.
  • Antihypertensives prescribed to a patient with no BP-related condition.
  • Antidiabetics given to a patient with no documented blood-sugar condition.
  • Antidepressants/antipsychotics without a psychiatric/neurological indication.
  • Chemotherapy agents for non-oncology patients.
  • Anticoagulants without a clotting or cardiovascular indication.
  • Corticosteroids without an inflammatory, allergic, or immune indication.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
B. DOSAGE SAFETY CHECKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Flag (⚠️ DOSAGE CONCERN) when dose exceeds accepted limits, e.g.:
  • Paracetamol > 4 g/day (3 g/day elderly/hepatic risk)
  • Ibuprofen > 3200 mg/day
  • Amoxicillin > 3000 mg/day for standard infections
  • Metformin > 2550 mg/day (or > 1000 mg/day with renal concerns)
  • Aspirin > 325 mg/day for cardiovascular prophylaxis
  • Omeprazole/PPIs > 40 mg/day for standard use
Also flag: sub-therapeutic dosing, adult doses for paediatric patients,
excessively long antibiotic courses (> 14 days without complex-infection note),
duration too short for the condition (e.g., < 6 months for TB).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
C. DRUG–DRUG INTERACTION CHECKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Flag (⚠️ INTERACTION RISK) for known high-risk pairs:
  • Warfarin + NSAIDs → bleeding risk
  • Warfarin + Fluoroquinolones/Metronidazole → INR elevation
  • ACE inhibitors + Potassium-sparing diuretics → hyperkalemia
  • SSRIs + Tramadol/MAOIs/Triptans → serotonin syndrome
  • Metformin + Nephrotoxic drugs → lactic acidosis risk
  • Statins + Fibrates (gemfibrozil) → rhabdomyolysis
  • Digoxin + Amiodarone → digoxin toxicity
  • QT-prolonging drugs together (azithromycin + chloroquine, etc.)
  • Corticosteroids + NSAIDs → GI bleed risk
  • Antihypertensives + PDE5 inhibitors → severe hypotension
  • Lithium + NSAIDs/Thiazides → lithium toxicity
  • Two or more anticoagulants without documented bridging rationale

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
D. PATIENT-SPECIFIC RISK FLAGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • Age < 18 → flag adult-only drugs (fluoroquinolones, tetracyclines < 8 yrs,
    high-dose NSAIDs, certain antidepressants).
  • Age > 65 → flag Beers Criteria drugs (long-acting benzodiazepines,
    anticholinergics, NSAIDs without PPI cover, first-gen antihistamines).
  • Gender mismatch without oncological/hormonal rationale.
  • Risk score > 60 → extra scrutiny on any new medication.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
E. SUSPICIOUS / UNUSUAL PRESCRIPTION FLAGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Flag (⚠️ UNUSUAL) when:
  • Controlled substance (opioids, benzodiazepines, stimulants) without a
    documented pain, anxiety, or ADHD diagnosis.
  • Multiple sedatives/CNS depressants co-prescribed.
  • Injectable drug in outpatient prescription without context.
  • Drug name appears misspelled or unrecognised — possible transcription error.
  • Duplicate therapy: two drugs from same class simultaneously.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
F. MANDATORY RESPONSE FORMAT FOR MEDICATION QUESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. SAFETY ASSESSMENT HEADER
   State: "✅ No concerns found" OR list each flag (⚠️ MISMATCH /
   ⚠️ DOSAGE CONCERN / ⚠️ INTERACTION RISK / ⚠️ UNUSUAL).

2. FOR EACH FLAG
   • What the concern is (plain language).
   • Why it matters clinically (brief, factual).
   • Action: "Please verify this with your doctor before taking this medication."

3. IF PRESCRIPTION APPEARS APPROPRIATE
   • Explain why it matches the condition.
   • Confirm dosage appears within normal range.
   • Note side effects to watch for.
   • Close with: "This is informational only. Always follow your doctor's
     guidance and report any side effects."

4. ANTI-BIAS RULES (STRICTLY ENFORCED)
   ✗ Do NOT say "Your prescription looks correct" without explicit reasoning.
   ✗ Do NOT use "Trust your doctor" as a complete answer to a safety question.
   ✗ Do NOT assume a prescription is fine because it exists in the system.
   ✗ Do NOT use vague reassurances like "You're in good hands."
   ✓ DO reason explicitly: condition → drug → dose → interactions.
   ✓ DO flag anything that raises a clinical question, even if uncertain.
   ✓ DO recommend doctor verification for any flagged item.
══════════════════════════════════════════════════════════════════════════════
"""

# ---------------------------------------------------------------------------
# SYMPTOM CHECKER FRAMEWORK
# ---------------------------------------------------------------------------

SYMPTOM_CHECKER_RULES = """
══════════════════════════════════════════════════════════════════════════════
SYMPTOM CHECKER MODE  (ACTIVATED — patient is describing symptoms)
══════════════════════════════════════════════════════════════════════════════

You are now in DIAGNOSTIC TRIAGE MODE. Follow this process strictly.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 1 — GATHER INFORMATION (if symptoms are vague)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If the patient's symptom description lacks enough detail, ask ONE focused
follow-up question before giving a verdict. Example: "How long have you had
this? Is it constant or comes and goes?"
Do NOT ask multiple questions at once — it overwhelms the patient.
If you have enough info, skip directly to Step 2.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 2 — ANALYSE SYMPTOMS USING PATIENT PROFILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Use the patient's age, gender, primary condition, risk score, and current
medications to personalise your analysis. The same symptom carries different
weight depending on the patient's profile.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 3 — TRIAGE VERDICT (MANDATORY — always end with one of these)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You MUST end your response with EXACTLY one of these verdict lines
(copy it exactly as shown — the app parses this line to show the alert button):

  TRIAGE_VERDICT: URGENT
  TRIAGE_VERDICT: MODERATE
  TRIAGE_VERDICT: MILD

Criteria:
  🔴 URGENT — Use when symptoms suggest a potentially life-threatening or
     rapidly worsening condition requiring immediate care:
     • Chest pain, pressure, or tightness
     • Difficulty breathing or shortness of breath at rest
     • Signs of stroke: sudden face drooping, arm weakness, speech difficulty
     • Severe allergic reaction: throat swelling, hives, collapse
     • Loss of consciousness or near-fainting
     • Uncontrolled bleeding
     • Severe abdominal pain
     • High fever (> 104°F / 40°C) with stiff neck, rash, or confusion
     • Seizures (first-time or prolonged)
     • Sudden severe headache ("worst headache of my life")
     • Blood in urine, stool, or vomit (significant amount)
     • Diabetic patient: very high/low blood sugar with symptoms

  🟡 MODERATE — Use when symptoms need professional evaluation soon
     but are not immediately life-threatening:
     • Persistent fever (> 2 days)
     • Worsening pain not controlled by current medication
     • New symptom not related to existing condition
     • Side effect from a prescribed medication that is bothersome
     • Symptoms that have lasted > 3–4 days with no improvement
     • Patient's risk score is HIGH (> 60) and any new symptom appears

  🟢 MILD — Use when symptoms are minor and self-manageable at home:
     • Common cold, mild sore throat, mild headache
     • Minor cuts or bruises
     • Mild stomach upset or nausea (1–2 episodes)
     • Known side effect of medication that is expected and tolerable
     • Symptom clearly explained by a known minor cause

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STEP 4 — RESPONSE FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Structure your reply as:

1. Brief empathetic acknowledgement (1 sentence).
2. What these symptoms may indicate — be informative but NOT alarmist.
   Use "may suggest" / "could be related to" — never claim a diagnosis.
3. Personalised context using their condition/age/risk/medications.
4. What to do RIGHT NOW (specific, actionable).
5. TRIAGE_VERDICT line (always last line of response).

ANTI-ALARMISM RULES:
  ✗ Do NOT say "You definitely have X disease."
  ✗ Do NOT catastrophise mild symptoms.
  ✓ DO be honest about urgency when warranted.
  ✓ DO use "may", "could", "might" for possible causes.
══════════════════════════════════════════════════════════════════════════════
"""

# Keywords that trigger medication safety mode
_MEDICATION_KEYWORDS = [
    "medicine", "medication", "drug", "tablet", "capsule", "dosage",
    "dose", "prescription", "prescribed", "safe", "correct", "right",
    "should i take", "can i take", "interaction", "side effect",
    "overdose", "mg", "ml", "antibiotic", "painkiller", "insulin",
    "injection", "syrup", "pill", "strip", "cream", "ointment", "drop",
    "is this okay", "is it safe", "is my medicine",
]

# Keywords that trigger symptom checker mode
_SYMPTOM_KEYWORDS = [
    "pain", "ache", "hurt", "fever", "temperature", "dizzy", "dizziness",
    "nausea", "vomit", "vomiting", "headache", "chest", "breathe",
    "breathing", "breath", "swelling", "swollen", "rash", "itch",
    "bleeding", "blood", "cough", "cold", "throat", "stomach", "abdomen",
    "abdominal", "weakness", "fatigue", "tired", "faint", "unconscious",
    "seizure", "shaking", "tremor", "vision", "blurred", "heart",
    "palpitation", "irregular", "burning", "numbness", "tingling",
    "diarrhea", "constipation", "urine", "urination", "joint", "back",
    "leg", "arm", "feel sick", "feeling sick", "not feeling well",
    "feeling unwell", "something wrong", "worried about", "i have",
    "i am having", "since yesterday", "since morning", "since last",
    "for 2 days", "for 3 days", "started", "suddenly",
]


def _is_symptom_query(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _SYMPTOM_KEYWORDS)


def _is_medication_query(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in _MEDICATION_KEYWORDS)


def extract_triage_verdict(response_text: str) -> str | None:
    """
    Parse the TRIAGE_VERDICT line from the AI response.
    Returns 'URGENT', 'MODERATE', 'MILD', or None.
    """
    for line in response_text.splitlines():
        line = line.strip()
        if line.startswith("TRIAGE_VERDICT:"):
            verdict = line.split(":", 1)[1].strip().upper()
            if verdict in ("URGENT", "MODERATE", "MILD"):
                return verdict
    return None


class ConversationAgent:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

    def _build_system_prompt(self, patient_id):
        import json as _json
        from datetime import date as _date
        from data.database import (
            get_mcq_responses as _get_mcq,
            get_patient_opd_bookings as _get_bookings,
            get_patient_alerts as _get_alerts,
        )

        patient = get_patient(patient_id)
        if not patient:
            return "You are a healthcare assistant with strict medical safety responsibilities."

        today_str     = _date.today().isoformat()
        prescriptions = get_patient_prescriptions(patient_id)
        med_info      = []
        prescription_history = []

        for pr in prescriptions:
            pr_date    = pr.get("created_at", "")[:10]
            meds_in_pr = []
            for m in pr.get("medicines", []):
                detail = (
                    f"{m['name']} {m['dosage']} "
                    f"for {m['duration_days']} days, timing: {m['timing']}"
                )
                med_info.append(detail)
                meds_in_pr.append(f"{m['name']} {m['dosage']} ({m['timing']})")
            notes = pr.get("doctor_notes", "")
            prescription_history.append(
                f"[{pr_date}] Prescribed: {', '.join(meds_in_pr)}"
                + (f" | Doctor notes: {notes}" if notes else "")
            )

        presc_block = (
            "\n".join(prescription_history)
            if prescription_history
            else "No prescriptions yet."
        )

        # ── Check-in history ──────────────────────────────────────────────────
        mcq_rows = _get_mcq(patient_id, limit=7)
        statuses = [r["status"]      for r in mcq_rows[:5]]
        scores   = [r["total_score"] for r in mcq_rows[:5]]

        if len(scores) >= 4:
            half     = len(scores) // 2
            first_h  = sum(scores[:half]) / half
            second_h = sum(scores[half:]) / (len(scores) - half)
            trend = ("improving" if second_h > first_h
                     else "worsening" if second_h < first_h
                     else "stable")
        elif scores:
            trend = statuses[0].lower() if statuses else "stable"
        else:
            trend = "no check-in data yet"

        # Adherence
        missed_dates = []
        for r in mcq_rows:
            adh = (r.get("adherence_status") or "").lower()
            if any(kw in adh for kw in ["miss", "skip", "forgot", "not tak", "no"]):
                missed_dates.append(r["date"])

        # Symptoms from MCQs
        symptoms = []
        for r in mcq_rows[:5]:
            try:
                rd = _json.loads(r.get("responses_json") or "{}")
                for q in rd.values():
                    if isinstance(q, dict):
                        sym = q.get("symptoms") or q.get("answer") or ""
                        if sym and isinstance(sym, str) and len(sym) > 3:
                            symptoms.append(sym)
            except Exception:
                pass

        # Side effects
        side_effects = []
        for r in mcq_rows[:5]:
            try:
                se = _json.loads(r.get("side_effects") or "[]")
                if isinstance(se, list):
                    side_effects.extend(se)
            except Exception:
                pass

        # ── Upcoming appointment ──────────────────────────────────────────────
        bookings      = _get_bookings(patient_id)
        upcoming_appt = None
        for b in sorted(bookings, key=lambda x: x.get("slot_date", "")):
            if b.get("slot_date", "") >= today_str and b.get("status") not in ("cancelled",):
                upcoming_appt = (
                    f"Dr. {b.get('doctor_name', b.get('doctor_id', '?'))} "
                    f"on {b['slot_date']} at {b.get('start_time', '?')}"
                )
                break

        # ── Active alerts ─────────────────────────────────────────────────────
        all_alerts   = _get_alerts(patient_id)
        unresolved   = [a for a in all_alerts if not a.get("resolved")]
        high_alerts  = [a for a in unresolved if a.get("severity") == "high"]
        alert_summary = (
            f"{len(unresolved)} active ({len(high_alerts)} high-priority)"
            if unresolved else "None"
        )

        doctor_name = patient.get("doctor_name") or patient.get("doctor_id") or "not assigned"

        context = f"""You are a critical-thinking AI healthcare assistant for patient {patient['name']}.
Your primary obligation is patient safety — not reassurance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATIENT PROFILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name            : {patient['name']}
Age             : {patient['age']}
Gender          : {patient['gender']}
Condition       : {patient['disease']}
Assigned Doctor : Dr. {doctor_name}
Visit Date      : {patient.get('visit_date', 'N/A')}
Risk Level      : {patient.get('risk_level', 'low').upper()} (Score: {patient.get('risk_score', 0)}/100)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEALTH TREND & CHECK-IN HISTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Overall Trend   : {trend.upper()}
Recent Statuses : {', '.join(statuses) if statuses else 'No check-ins yet'}
Recent Scores   : {', '.join(str(s) for s in scores) if scores else 'N/A'}
Adherence       : {'Missed doses on: ' + ', '.join(missed_dates[:3]) if missed_dates else 'Good — no missed doses'}
Reported Symptoms : {'; '.join(list(set(symptoms))[:5]) if symptoms else 'None reported'}
Side Effects      : {'; '.join(list(set(side_effects))[:4]) if side_effects else 'None reported'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
APPOINTMENTS & ALERTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Upcoming Appointment : {upcoming_appt or 'None scheduled'}
Active Alerts        : {alert_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRESCRIPTION HISTORY (as recorded in system)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{presc_block}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CURRENT ACTIVE MEDICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{'; '.join(med_info) if med_info else 'None prescribed yet'}

TODAY: {today_str}

{SAFETY_RULES}"""
        return context

    def chat(self, patient_id, user_message):
        """
        Returns a dict: {"reply": str, "triage": str|None}
        triage is one of: "URGENT", "MODERATE", "MILD", or None
        """
        if not GROQ_API_KEY or GROQ_API_KEY.strip() == "":
            msg = (
                "⚠️ AI service is not configured. "
                "Please add your **GROQ_API_KEY** via Streamlit Cloud → App Settings → Secrets and restart the app."
            )
            save_chat_message(patient_id, "user", user_message)
            save_chat_message(patient_id, "assistant", msg)
            return {"reply": msg, "triage": None}

        history = get_chat_history(patient_id, MAX_CHAT_HISTORY)
        messages = [{"role": "system", "content": self._build_system_prompt(patient_id)}]

        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})

        messages.append({"role": "user", "content": user_message})
        save_chat_message(patient_id, "user", user_message)

        is_symptom = _is_symptom_query(user_message)
        is_med = _is_medication_query(user_message)

        # Inject symptom checker mode
        if is_symptom:
            messages.append({
                "role": "system",
                "content": SYMPTOM_CHECKER_RULES
            })

        # Inject medication safety reminder
        if is_med:
            messages.append({
                "role": "system",
                "content": (
                    "SAFETY REMINDER: This message involves a medication or prescription. "
                    "Apply the full Medical Safety Validation Framework above. "
                    "Do NOT confirm correctness without explicit reasoning. "
                    "Check: (1) condition–drug match, (2) dosage range, "
                    "(3) drug interactions, (4) patient-specific risks (age, gender, risk score). "
                    "Flag any concern with ⚠️ and advise doctor verification."
                )
            })

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.3,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = _safe_extract_text(data)

            if content is not None:
                assistant_reply = content
            elif data.get("error"):
                err_msg = data["error"].get("message", "Unknown API error")
                assistant_reply = f"AI service error: {err_msg}. Please try again."
            else:
                assistant_reply = (
                    "Received an unexpected response from the AI service. Please try again."
                )

        except requests.exceptions.Timeout:
            assistant_reply = "Request timed out. Please try again in a moment."
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            if status_code == 401:
                assistant_reply = (
                    "❌ GROQ API key is invalid or expired (401 Unauthorized). "
                    "Please update **GROQ_API_KEY** via Streamlit Cloud → App Settings → Secrets with a valid key from "
                    "https://console.groq.com/keys and restart the app."
                )
            else:
                assistant_reply = f"Service error ({status_code}). Please try again shortly."
        except (KeyError, IndexError, ValueError) as e:
            assistant_reply = f"Response parsing error. Please try again. ({str(e)[:60]})"
        except Exception as e:
            assistant_reply = (
                f"I'm having trouble connecting right now. Please try again shortly. "
                f"({str(e)[:50]})"
            )

        # Extract triage verdict if this was a symptom query
        triage = None
        if is_symptom:
            triage = extract_triage_verdict(assistant_reply)
            # Strip the TRIAGE_VERDICT line from the visible reply
            clean_lines = [
                l for l in assistant_reply.splitlines()
                if not l.strip().startswith("TRIAGE_VERDICT:")
            ]
            assistant_reply = "\n".join(clean_lines).strip()

        save_chat_message(patient_id, "assistant", assistant_reply)
        return {"reply": assistant_reply, "triage": triage}

    def analyze_chat_for_concerns(self, patient_id):
        history = get_chat_history(patient_id, 10)
        if len(history) < 2:
            return None

        recent_text = " ".join([h["content"] for h in history if h["role"] == "user"])

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a medical alert system. Analyze patient messages for concerning "
                    "symptoms. Respond with JSON only: "
                    '{"concern": true/false, "severity": "low/medium/high", "summary": "brief summary"}'
                ),
            },
            {"role": "user", "content": f"Patient messages: {recent_text}"},
        ]

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 200,
                    "temperature": 0.2,
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            content = _safe_extract_text(data)
            if content is None:
                return None
            text = content.strip().strip("```json").strip("```").strip()
            return json.loads(text)
        except Exception:
            return None
