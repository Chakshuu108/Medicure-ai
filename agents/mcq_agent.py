import requests
import json
from data.database import (
    get_patient, get_patient_prescriptions,
    save_mcq_set, get_mcq_set
)
from core.config import GROQ_API_KEY, GROQ_MODEL


class MCQAgent:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

    def generate_mcqs(self, patient_id, date_str, force_regenerate=False):
        """Generate or retrieve MCQs for a patient on a given date."""
        # Return cached if exists and not forced
        if not force_regenerate:
            existing = get_mcq_set(patient_id, date_str)
            if existing:
                return json.loads(existing["questions_json"])

        patient = get_patient(patient_id)
        if not patient:
            return self._fallback_mcqs()

        prescriptions = get_patient_prescriptions(patient_id)
        med_names = []
        for pr in prescriptions:
            for m in pr.get("medicines", []):
                med_names.append(f"{m['name']} ({m['dosage']}, {m['timing']})")

        prompt = f"""You are a clinical AI. Generate exactly 5 MCQ questions for a daily health check-in for this patient.

Patient Details:
- Disease/Condition: {patient['disease']}
- Age: {patient['age']}, Gender: {patient['gender']}
- Current Medications: {', '.join(med_names) if med_names else 'None yet'}

Requirements:
- 2 questions about symptom improvement/worsening
- 1 question about medication adherence (taken or missed)
- 1 question about side effects
- 1 question about general wellbeing

Each question must have exactly 3 options with scores:
- Improved/Taken/Good → score: +1
- No Change/Partial → score: 0
- Worsened/Missed/Bad → score: -1

Return ONLY valid JSON array, no markdown, no explanation:
[
  {{
    "id": 1,
    "category": "symptom",
    "question": "How are your <specific symptom related to {patient['disease']}> today?",
    "options": [
      {{"text": "Better than yesterday", "score": 1, "tag": "improved"}},
      {{"text": "About the same", "score": 0, "tag": "stable"}},
      {{"text": "Worse than yesterday", "score": -1, "tag": "worsened"}}
    ]
  }},
  ...
]"""

        messages = [
            {"role": "system", "content": "You are a clinical MCQ generator. Return only valid JSON arrays."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"model": GROQ_MODEL, "messages": messages, "max_tokens": 1500, "temperature": 0.4}
            )
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return None
            text = (choices[0].get("message") or {}).get("content") or ""
            text = text.strip()
            # Strip markdown fences
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()
            questions = json.loads(text)
            # Validate structure
            if not isinstance(questions, list) or len(questions) == 0:
                raise ValueError("Invalid MCQ format")

            doctor_id = patient.get("doctor_id")
            save_mcq_set(patient_id, doctor_id, json.dumps(questions), date_str)
            return questions

        except Exception as e:
            fallback = self._fallback_mcqs(patient.get("disease", "your condition"), med_names)
            doctor_id = patient.get("doctor_id")
            save_mcq_set(patient_id, doctor_id, json.dumps(fallback), date_str)
            return fallback

    def _fallback_mcqs(self, disease="your condition", med_names=None):
        med_str = med_names[0] if med_names else "your medication"
        return [
            {
                "id": 1,
                "category": "symptom",
                "question": f"How are your primary symptoms related to {disease} today?",
                "options": [
                    {"text": "Noticeably better", "score": 1, "tag": "improved"},
                    {"text": "About the same", "score": 0, "tag": "stable"},
                    {"text": "Worse than before", "score": -1, "tag": "worsened"}
                ]
            },
            {
                "id": 2,
                "category": "symptom",
                "question": "How is your pain or discomfort level today compared to yesterday?",
                "options": [
                    {"text": "Reduced significantly", "score": 1, "tag": "improved"},
                    {"text": "Unchanged", "score": 0, "tag": "stable"},
                    {"text": "Increased", "score": -1, "tag": "worsened"}
                ]
            },
            {
                "id": 3,
                "category": "adherence",
                "question": f"Have you taken {med_str} as prescribed today?",
                "options": [
                    {"text": "Yes, all doses on time", "score": 1, "tag": "taken"},
                    {"text": "Partially (missed one dose)", "score": 0, "tag": "partial"},
                    {"text": "No, missed today's dose", "score": -1, "tag": "missed"}
                ]
            },
            {
                "id": 4,
                "category": "side_effect",
                "question": "Are you experiencing any side effects from your medications?",
                "options": [
                    {"text": "No side effects", "score": 1, "tag": "none"},
                    {"text": "Mild, manageable effects", "score": 0, "tag": "mild"},
                    {"text": "Significant side effects", "score": -1, "tag": "significant"}
                ]
            },
            {
                "id": 5,
                "category": "wellbeing",
                "question": "How would you rate your overall wellbeing today?",
                "options": [
                    {"text": "Feeling good / improving", "score": 1, "tag": "good"},
                    {"text": "Neutral / okay", "score": 0, "tag": "neutral"},
                    {"text": "Poor / struggling", "score": -1, "tag": "poor"}
                ]
            }
        ]

    def compute_status(self, total_score):
        if total_score > 0:
            return "Improving"
        elif total_score == 0:
            return "Stable"
        else:
            return "Worsening"

    def get_feedback(self, status):
        return {
            "Improving": {
                "message": "Great progress! Continue your medication as prescribed.",
                "icon": "✅",
                "color": "#34D399",
                "action": "Continue medication"
            },
            "Stable": {
                "message": "Your condition is stable. Monitor closely and follow your prescription.",
                "icon": "⚠️",
                "color": "#FBBF24",
                "action": "Monitor closely"
            },
            "Worsening": {
                "message": "Your symptoms suggest worsening. Please visit your doctor immediately.",
                "icon": "❌",
                "color": "#F87171",
                "action": "Visit doctor immediately"
            }
        }.get(status, {})

    def extract_response_details(self, questions, selected_options):
        """Extract key symptoms, adherence, and side effects from responses."""
        symptoms = []
        adherence = "Unknown"
        side_effects = []

        for q in questions:
            qid = q["id"]
            selected_idx = selected_options.get(str(qid))
            if selected_idx is None:
                continue
            try:
                option = q["options"][selected_idx]
            except (IndexError, TypeError):
                continue

            tag = option.get("tag", "")
            category = q.get("category", "")

            if category == "symptom":
                if tag in ("worsened", "stable", "improved"):
                    symptoms.append(f"{q['question']} → {option['text']}")
            elif category == "adherence":
                adherence = option["text"]
            elif category == "side_effect":
                if tag in ("mild", "significant"):
                    side_effects.append(option["text"])

        return symptoms, adherence, side_effects
