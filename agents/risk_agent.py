import time
import requests
import json
from data.database import get_patient, get_patient_prescriptions, get_chat_history, update_patient_risk
from core.config import GROQ_API_KEY, GROQ_MODEL

# Cache risk results in memory — re-evaluate only every 5 minutes per patient
_RISK_CACHE: dict = {}  # patient_id -> (timestamp, result)
_RISK_TTL_SECS = 300


class RiskScoringAgent:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

    def _score_from_level(self, level):
        return {"low": 20, "medium": 55, "high": 85}.get(level, 20)

    def evaluate(self, patient_id):
        # Return cached result if still fresh
        cached = _RISK_CACHE.get(patient_id)
        if cached:
            ts, result = cached
            if time.time() - ts < _RISK_TTL_SECS:
                return result

        patient = get_patient(patient_id)
        prescriptions = get_patient_prescriptions(patient_id)
        chat = get_chat_history(patient_id, 10)
        
        med_count = sum(len(p.get("medicines", [])) for p in prescriptions)
        chat_concerns = " ".join([h["content"] for h in chat if h["role"] == "user"][-5:])
        
        prompt = f"""Evaluate health risk for:
Patient: {patient['name']}, Age: {patient['age']}, Disease: {patient['disease']}
Medications count: {med_count}
Recent patient messages: {chat_concerns if chat_concerns else 'No messages yet'}

Respond ONLY with valid JSON: {{"risk_score": <0-100>, "risk_level": "<low|medium|high>", "reasoning": "<brief>"}}"""

        messages = [
            {"role": "system", "content": "You are a medical risk assessment AI. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={"model": GROQ_MODEL, "messages": messages, "max_tokens": 200, "temperature": 0.1}
            )
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                return {"score": 20, "level": "low", "reasoning": "API returned no choices"}
            text = (choices[0].get("message") or {}).get("content") or ""
            text = text.strip().strip("```json").strip("```").strip()
            result = json.loads(text)
            score = int(result.get("risk_score", 20))
            level = result.get("risk_level", "low")
            update_patient_risk(patient_id, score, level)
            risk_result = {"score": score, "level": level, "reasoning": result.get("reasoning", "")}
            _RISK_CACHE[patient_id] = (time.time(), risk_result)
            return risk_result
        except Exception as e:
            age_factor = min(int(patient.get("age", 30)) // 10, 3) * 10
            score = 20 + age_factor + (med_count * 5)
            score = min(score, 100)
            level = "high" if score >= 70 else "medium" if score >= 40 else "low"
            update_patient_risk(patient_id, score, level)
            risk_result = {"score": score, "level": level, "reasoning": "Calculated from baseline factors"}
            _RISK_CACHE[patient_id] = (time.time(), risk_result)
            return risk_result

    def batch_evaluate(self, patient_ids):
        results = {}
        for pid in patient_ids:
            results[pid] = self.evaluate(pid)
        return results
