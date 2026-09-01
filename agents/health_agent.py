import requests
import json
from data.database import get_patient, get_patient_prescriptions, get_chat_history, get_all_medicines_for_patient
from core.config import GROQ_API_KEY, GROQ_MODEL
from datetime import datetime, date

class HealthEvaluationAgent:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

    def evaluate_adherence(self, patient_id):
        medicines = get_all_medicines_for_patient(patient_id)
        today = date.today()
        active_meds = []
        expired_meds = []
        
        for m in medicines:
            start = datetime.fromisoformat(m["start_date"]).date() if m.get("start_date") else today
            end_day = (today - start).days
            if end_day <= m.get("duration_days", 7):
                active_meds.append(m)
            else:
                expired_meds.append(m)
        
        return {
            "active_medications": len(active_meds),
            "completed_medications": len(expired_meds),
            "active_list": active_meds,
            "treatment_ongoing": len(active_meds) > 0
        }

    def detect_behavioral_trends(self, patient_id):
        chat = get_chat_history(patient_id, 20)
        if not chat:
            return {"trend": "insufficient_data", "signals": []}
        
        user_messages = [h["content"] for h in chat if h["role"] == "user"]
        if not user_messages:
            return {"trend": "no_engagement", "signals": []}
        
        concern_keywords = ["worse", "pain", "fever", "vomiting", "dizzy", "chest", "breathing", "severe", "emergency"]
        improvement_keywords = ["better", "improving", "feeling good", "recovered", "well", "normal"]
        
        concern_count = sum(1 for m in user_messages for k in concern_keywords if k in m.lower())
        improvement_count = sum(1 for m in user_messages for k in improvement_keywords if k in m.lower())
        
        if concern_count > improvement_count:
            trend = "worsening"
        elif improvement_count > concern_count:
            trend = "improving"
        else:
            trend = "stable"
        
        signals = []
        if concern_count > 2:
            signals.append("Multiple symptom complaints detected")
        if improvement_count > 2:
            signals.append("Patient reporting improvement")
        
        return {"trend": trend, "signals": signals, "concern_score": concern_count, "improvement_score": improvement_count}

    def generate_health_summary(self, patient_id):
        patient = get_patient(patient_id)
        adherence = self.evaluate_adherence(patient_id)
        trends = self.detect_behavioral_trends(patient_id)
        chat = get_chat_history(patient_id, 5)
        
        recent_msgs = " | ".join([h["content"] for h in chat if h["role"] == "user"][-3:])
        
        prompt = f"""Generate a clinical health summary for:
Patient: {patient['name']}, Age {patient['age']}, Condition: {patient['disease']}
Active medications: {adherence['active_medications']}
Behavioral trend: {trends['trend']}
Recent messages: {recent_msgs if recent_msgs else 'None'}
Signals: {', '.join(trends['signals']) if trends['signals'] else 'None'}

Provide a concise 2-3 sentence clinical assessment."""

        messages = [
            {"role": "system", "content": "You are a clinical assessment AI. Be concise and clinical."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"model": GROQ_MODEL, "messages": messages, "max_tokens": 300, "temperature": 0.3}
            )
            data = response.json()
            choices = data.get("choices") or []
            if choices:
                return (choices[0].get("message") or {}).get("content") or ""
            return ""
        except:
            return f"Patient {patient['name']} is on {adherence['active_medications']} active medication(s). Trend appears {trends['trend']}."
