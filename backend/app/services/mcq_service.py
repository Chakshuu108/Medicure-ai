"""Dynamic daily MCQ generation — disease, meds, and history aware."""

import json
from datetime import date, timedelta

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings, is_groq_configured
from app.models import MCQResponse, MCQSet, Patient, Prescription


def compute_status(total_score: int) -> str:
    if total_score > 0:
        return "Improving"
    if total_score == 0:
        return "Stable"
    return "Worsening"


def get_feedback(status: str) -> dict:
    return {
        "Improving": {
            "message": "Great progress! Continue your medication as prescribed.",
            "icon": "✅",
            "color": "#34D399",
            "action": "Continue medication",
        },
        "Stable": {
            "message": "Your condition is stable. Monitor closely and follow your prescription.",
            "icon": "⚠️",
            "color": "#FBBF24",
            "action": "Monitor closely",
        },
        "Worsening": {
            "message": "Your symptoms suggest worsening. Please visit your doctor soon.",
            "icon": "❌",
            "color": "#F87171",
            "action": "Visit doctor",
        },
    }.get(status, {})


def _normalize_questions(raw) -> list[dict]:
    if isinstance(raw, dict):
        raw = raw.get("questions", [])
    if not isinstance(raw, list):
        return []
    normalized = []
    for i, q in enumerate(raw):
        opts = q.get("options", [])
        norm_opts = []
        for j, opt in enumerate(opts):
            if isinstance(opt, dict):
                norm_opts.append({
                    "text": opt.get("text", str(opt)),
                    "score": int(opt.get("score", 1 - j)),
                    "tag": opt.get("tag", ""),
                })
            else:
                scores = [1, 0, -1, -1]
                norm_opts.append({"text": str(opt), "score": scores[j] if j < len(scores) else 0, "tag": ""})
        normalized.append({
            "id": q.get("id", i + 1),
            "category": q.get("category") or q.get("type", "wellbeing"),
            "question": q.get("question", ""),
            "options": norm_opts,
        })
    return normalized


def _fallback_mcqs(disease: str = "your condition", med_names: list[str] | None = None) -> list[dict]:
    med_str = med_names[0] if med_names else "your medication"
    return [
        {
            "id": 1, "category": "symptom",
            "question": f"How are your primary symptoms related to {disease} today?",
            "options": [
                {"text": "Noticeably better", "score": 1, "tag": "improved"},
                {"text": "About the same", "score": 0, "tag": "stable"},
                {"text": "Worse than before", "score": -1, "tag": "worsened"},
            ],
        },
        {
            "id": 2, "category": "symptom",
            "question": "How is your pain or discomfort level compared to yesterday?",
            "options": [
                {"text": "Reduced", "score": 1, "tag": "improved"},
                {"text": "Unchanged", "score": 0, "tag": "stable"},
                {"text": "Increased", "score": -1, "tag": "worsened"},
            ],
        },
        {
            "id": 3, "category": "adherence",
            "question": f"Have you taken {med_str} as prescribed today?",
            "options": [
                {"text": "Yes, all doses on time", "score": 1, "tag": "taken"},
                {"text": "Partially", "score": 0, "tag": "partial"},
                {"text": "No, missed dose(s)", "score": -1, "tag": "missed"},
            ],
        },
        {
            "id": 4, "category": "side_effect",
            "question": "Any side effects from your medications?",
            "options": [
                {"text": "None", "score": 1, "tag": "none"},
                {"text": "Mild", "score": 0, "tag": "mild"},
                {"text": "Significant", "score": -1, "tag": "significant"},
            ],
        },
        {
            "id": 5, "category": "wellbeing",
            "question": "Overall wellbeing today?",
            "options": [
                {"text": "Good / improving", "score": 1, "tag": "good"},
                {"text": "Neutral", "score": 0, "tag": "neutral"},
                {"text": "Poor / struggling", "score": -1, "tag": "poor"},
            ],
        },
    ]


def extract_response_details(questions: list[dict], selected_options: dict) -> tuple[list[str], str, list[str]]:
    symptoms: list[str] = []
    adherence = "Unknown"
    side_effects: list[str] = []

    for q in questions:
        qid = str(q["id"])
        idx = selected_options.get(qid)
        if idx is None:
            idx = selected_options.get(q["id"])
        if idx is None:
            continue
        try:
            option = q["options"][int(idx)]
        except (IndexError, TypeError, ValueError):
            continue
        tag = option.get("tag", "")
        category = q.get("category", "")
        if category == "symptom":
            symptoms.append(f"{q['question']} → {option['text']}")
        elif category == "adherence":
            adherence = option["text"]
        elif category == "side_effect" and tag in ("mild", "significant"):
            side_effects.append(option["text"])
    return symptoms, adherence, side_effects


def compute_total_score(questions: list[dict], selected_options: dict) -> int:
    total = 0
    for q in questions:
        qid = str(q["id"])
        idx = selected_options.get(qid)
        if idx is None:
            idx = selected_options.get(q["id"])
        if idx is None:
            continue
        try:
            total += int(q["options"][int(idx)].get("score", 0))
        except (IndexError, TypeError, ValueError):
            pass
    return total


async def _get_med_names(db: AsyncSession, patient_id: str) -> list[str]:
    result = await db.execute(
        select(Prescription)
        .options(selectinload(Prescription.medicines))
        .where(Prescription.patient_id == patient_id)
        .order_by(Prescription.created_at.desc())
        .limit(1)
    )
    rx = result.scalar_one_or_none()
    if not rx:
        return []
    return [f"{m.name} ({m.dosage}, {m.timing})" for m in rx.medicines]


async def _get_recent_context(db: AsyncSession, patient_id: str) -> str:
    result = await db.execute(
        select(MCQResponse)
        .where(MCQResponse.patient_id == patient_id)
        .order_by(MCQResponse.date.desc())
        .limit(3)
    )
    rows = result.scalars().all()
    if not rows:
        return "No prior check-ins."
    parts = []
    for r in rows:
        parts.append(f"{r.date}: score {r.total_score}, status {r.status}, adherence {r.adherence_status}")
    return "; ".join(parts)


async def generate_today_mcqs(db: AsyncSession, patient: Patient) -> dict:
    today = date.today().isoformat()
    result = await db.execute(
        select(MCQSet).where(MCQSet.patient_id == patient.id, MCQSet.date == today)
    )
    existing = result.scalar_one_or_none()
    if existing:
        questions = _normalize_questions(existing.questions_json)
        return {"questions": questions, "date": today, "cached": True}

    med_names = await _get_med_names(db, patient.id)
    recent = await _get_recent_context(db, patient.id)

    questions = _fallback_mcqs(patient.disease or "your condition", med_names)

    if is_groq_configured():
        settings = get_settings()
        llm = ChatGroq(api_key=settings.groq_api_key, model=settings.groq_model, temperature=0.4)
        prompt = f"""Generate exactly 5 MCQ questions for a daily health check-in.

Patient:
- Disease: {patient.disease}
- Age: {patient.age}, Gender: {patient.gender}
- Medications: {', '.join(med_names) if med_names else 'None'}
- Recent check-ins: {recent}

Requirements:
- 2 symptom questions specific to {patient.disease}
- 1 medication adherence question (use actual medicine names if available)
- 1 side effect question
- 1 general wellbeing question
- Reference yesterday's trend when relevant
- Each question: exactly 3 options with score +1, 0, -1 and a tag

Return ONLY a JSON array:
[{{"id":1,"category":"symptom","question":"...","options":[{{"text":"...","score":1,"tag":"improved"}},...]}}]"""

        try:
            resp = await llm.ainvoke([
                SystemMessage(content="Clinical MCQ generator. Return only valid JSON array."),
                HumanMessage(content=prompt),
            ])
            text = (resp.content or "").replace("```json", "").replace("```", "").strip()
            parsed = json.loads(text)
            questions = _normalize_questions(parsed)
            if len(questions) < 3:
                raise ValueError("Too few questions")
        except Exception:
            questions = _fallback_mcqs(patient.disease or "your condition", med_names)
    else:
        questions = _fallback_mcqs(patient.disease or "your condition", med_names)

    mcq_set = MCQSet(
        patient_id=patient.id,
        doctor_id=patient.doctor_id,
        date=today,
        questions_json={"questions": questions},
    )
    db.add(mcq_set)
    await db.flush()
    return {"questions": questions, "date": today, "cached": False}


async def get_mcq_trends(db: AsyncSession, patient_id: str, days: int = 30) -> dict:
    today = date.today()
    start = today - timedelta(days=days - 1)

    result = await db.execute(
        select(MCQResponse)
        .where(MCQResponse.patient_id == patient_id, MCQResponse.date >= start.isoformat())
        .order_by(MCQResponse.date.asc())
    )
    by_date = {r.date: r for r in result.scalars()}

    points = []
    rolling_scores: list[int] = []
    current = start
    while current <= today:
        ds = current.isoformat()
        if ds in by_date:
            r = by_date[ds]
            rolling_scores.append(r.total_score)
            window = rolling_scores[-3:]
            rolling_avg = round(sum(window) / len(window), 2)
            points.append({
                "date": ds,
                "total_score": r.total_score,
                "status": r.status,
                "missed": False,
                "rolling_avg": rolling_avg,
            })
        else:
            points.append({
                "date": ds,
                "total_score": None,
                "status": "Missed",
                "missed": True,
                "rolling_avg": None,
            })
        current += timedelta(days=1)

    completed = [p for p in points if not p["missed"]]
    missed_count = sum(1 for p in points if p["missed"])
    latest_status = completed[-1]["status"] if completed else "No data"
    trend = "stable"
    if len(completed) >= 3:
        recent = [p["total_score"] for p in completed[-3:]]
        if all(recent[i] <= recent[i + 1] for i in range(len(recent) - 1)) and recent[-1] > recent[0]:
            trend = "improving"
        elif all(recent[i] >= recent[i + 1] for i in range(len(recent) - 1)) and recent[-1] < recent[0]:
            trend = "worsening"

    return {
        "points": points,
        "summary": {
            "completed_days": len(completed),
            "missed_days": missed_count,
            "latest_status": latest_status,
            "trend": trend,
        },
    }
