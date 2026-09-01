"""Clinical alerts — doctor notifications with plain-English summaries."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, Doctor, Patient
from app.services.email_service import send_doctor_clinical_alert_email

# Internal/system alerts — never shown to doctors
PATIENT_ONLY_ALERT_TYPES = frozenset({
    "missed_mcq_reminder",
})

ALERT_TYPE_LABELS: dict[str, str] = {
    "mcq_health_check": "Daily Health Check",
    "Health Guardian — Pattern Detected": "Health Guardian",
    "Health Guardian — Missed Check-ins": "Missed Check-ins",
    "patient_reported_symptoms": "Symptoms Reported",
    "high_risk": "Health Risk",
    "worsening": "Worsening Health",
    "emergency": "Urgent Concern",
    "risk_assessment": "Health Risk",
    "agent_opd_booked": "Appointment Booked",
}

SEVERITY_LABELS = {
    "severe": "Severe",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}


def normalize_severity(severity: str) -> str:
    s = (severity or "medium").lower().strip()
    if s in ("urgent", "critical", "emergency"):
        return "severe"
    if s in SEVERITY_LABELS:
        return s
    return "medium"


def severity_label(severity: str) -> str:
    return SEVERITY_LABELS.get(normalize_severity(severity), "Medium")


def alert_type_label(alert_type: str) -> str:
    if alert_type in ALERT_TYPE_LABELS:
        return ALERT_TYPE_LABELS[alert_type]
    return alert_type.replace("_", " ").replace("—", "-").strip()


def _first_sentence(text: str, max_len: int = 140) -> str:
    cleaned = (text or "").strip().replace("\n", " ")
    if not cleaned:
        return ""
    for sep in (". ", "! ", "? "):
        if sep in cleaned:
            cleaned = cleaned.split(sep, 1)[0] + sep.strip()
            break
    if len(cleaned) > max_len:
        return cleaned[: max_len - 3] + "..."
    return cleaned


def build_alert_summary(
    alert_type: str,
    message: str,
    severity: str,
    patient_name: str | None = None,
) -> str:
    """Short plain-English summary for dashboards."""
    topic = alert_type_label(alert_type)
    snippet = _first_sentence(message)
    level = severity_label(severity)

    templates = {
        "emergency": "Patient reported an urgent health concern that needs immediate attention.",
        "patient_reported_symptoms": "Patient reported new or worsening symptoms.",
        "mcq_health_check": "Daily health check showed a concerning result.",
        "Health Guardian — Pattern Detected": "Health Guardian noticed a worrying pattern in check-ins.",
        "Health Guardian — Missed Check-ins": "Patient has missed several daily health check-ins.",
        "worsening": "Patient's health trend appears to be getting worse.",
        "high_risk": "Patient's health risk level has increased.",
    }

    base = templates.get(alert_type, f"{topic} needs review.")
    if snippet and alert_type not in ("emergency",):
        base = f"{base} {snippet}"
    if patient_name:
        return f"{patient_name}: {base}"
    return base


def is_doctor_facing(alert_type: str) -> bool:
    return alert_type not in PATIENT_ONLY_ALERT_TYPES


def classify_chat_urgency(message: str) -> dict | None:
    """Rule-based urgency detection for chat messages."""
    msg = (message or "").lower()
    rules = [
        (
            ("heart attack", "heart attac", "chest pain", "cardiac arrest", "my chest hurts"),
            "severe",
            "emergency",
            "Patient reported possible heart attack or severe chest pain.",
        ),
        (
            ("can't breathe", "cannot breathe", "not breathing", "difficulty breathing", "choking"),
            "severe",
            "emergency",
            "Patient reported serious breathing difficulty.",
        ),
        (
            ("stroke", "face drooping", "slurred speech", "sudden numbness"),
            "severe",
            "emergency",
            "Patient reported possible stroke symptoms.",
        ),
        (
            ("unconscious", "passed out", "fainted", "severe bleeding", "suicide", "overdose"),
            "severe",
            "emergency",
            "Patient reported a critical emergency situation.",
        ),
        (
            ("severe pain", "intense pain", "unbearable pain", "emergency", "911", "112", "108"),
            "high",
            "patient_reported_symptoms",
            "Patient reported severe symptoms that need prompt medical review.",
        ),
        (
            ("fever", "headache", "pain", "dizzy", "vomit", "nausea", "symptom", "hurt", "sick", "worse"),
            "medium",
            "patient_reported_symptoms",
            "Patient reported symptoms through the health chat.",
        ),
    ]
    for keywords, severity, alert_type, summary in rules:
        if any(k in msg for k in keywords):
            return {
                "severity": severity,
                "alert_type": alert_type,
                "summary": summary,
                "triage": "URGENT" if severity == "severe" else "MODERATE" if severity == "high" else "MILD",
            }
    return None


async def create_clinical_alert(
    db: AsyncSession,
    *,
    patient_id: str,
    doctor_id: str | None,
    alert_type: str,
    message: str,
    severity: str = "medium",
    notify_doctor: bool = True,
) -> Alert:
    """Create a clinical alert and optionally email the assigned doctor."""
    severity = normalize_severity(severity)
    if not is_doctor_facing(alert_type):
        notify_doctor = False

    if not doctor_id:
        pat_result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = pat_result.scalar_one_or_none()
        if patient:
            doctor_id = patient.doctor_id

    alert = Alert(
        patient_id=patient_id,
        doctor_id=doctor_id,
        alert_type=alert_type,
        message=message,
        severity=severity,
    )
    db.add(alert)
    await db.flush()

    if notify_doctor and doctor_id:
        doc_result = await db.execute(select(Doctor).where(Doctor.id == doctor_id))
        doctor = doc_result.scalar_one_or_none()
        pat_result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = pat_result.scalar_one_or_none()
        if doctor and patient and doctor.email:
            summary = build_alert_summary(alert_type, message, severity, patient.name)
            await send_doctor_clinical_alert_email(
                doctor_name=doctor.name,
                doctor_email=doctor.email,
                patient_name=patient.name,
                patient_code=patient.patient_code,
                disease=patient.disease or "Not specified",
                alert_type=alert_type_label(alert_type),
                severity=severity_label(severity),
                summary=summary,
                full_message=message,
            )

    return alert


async def create_chat_symptom_alert(
    db: AsyncSession,
    *,
    patient_id: str,
    message: str,
) -> Alert | None:
    """Create a doctor alert from patient chat when symptoms/emergencies are detected."""
    urgency = classify_chat_urgency(message)
    if not urgency:
        return None

    pat_result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = pat_result.scalar_one_or_none()
    if not patient:
        return None

    detail = _first_sentence(message, 200) or urgency["summary"]
    full_message = (
        f"{urgency['summary']}\n\n"
        f"Patient said: \"{detail}\"\n\n"
        f"Please review this patient in the MediCure alerts tab."
    )
    return await create_clinical_alert(
        db,
        patient_id=patient_id,
        doctor_id=patient.doctor_id,
        alert_type=urgency["alert_type"],
        message=full_message,
        severity=urgency["severity"],
    )


def serialize_alert(
    alert: Alert,
    patient_name: str | None = None,
    patient_code: str | None = None,
) -> dict:
    severity = normalize_severity(alert.severity)
    return {
        "id": alert.id,
        "patient_id": alert.patient_id,
        "patient_name": patient_name,
        "patient_code": patient_code,
        "alert_type": alert.alert_type,
        "alert_type_label": alert_type_label(alert.alert_type),
        "message": alert.message,
        "summary": build_alert_summary(
            alert.alert_type, alert.message, severity, patient_name,
        ),
        "severity": severity,
        "severity_label": severity_label(severity),
        "resolved": alert.resolved,
        "created_at": alert.created_at.isoformat(),
    }
