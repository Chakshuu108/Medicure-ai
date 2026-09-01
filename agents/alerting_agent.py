import time
from data.database import create_alert, get_alerts, resolve_alert, get_all_patients, get_patient
from agents.risk_agent import RiskScoringAgent
from agents.health_agent import HealthEvaluationAgent
from agents.conversation_agent import ConversationAgent

# Throttle: only run full alert check once every N seconds per patient
_ALERT_THROTTLE_SECS = 120
_last_alert_check: dict = {}  # patient_id -> timestamp


class AlertingAgent:
    def __init__(self):
        self.risk_agent = RiskScoringAgent()
        self.health_agent = HealthEvaluationAgent()
        self.conv_agent = ConversationAgent()

    def _get_doctor_id(self, patient_id):
        p = get_patient(patient_id)
        return p.get("doctor_id") if p else None

    def check_and_alert(self, patient_id):
        # Throttle expensive alert checks — skip if checked recently
        now = time.time()
        last = _last_alert_check.get(patient_id, 0)
        if now - last < _ALERT_THROTTLE_SECS:
            return []  # Skip — checked within the last 2 minutes
        _last_alert_check[patient_id] = now

        alerts_created = []
        doctor_id = self._get_doctor_id(patient_id)

        risk = self.risk_agent.evaluate(patient_id)
        if risk["level"] == "high":
            create_alert(
                patient_id,
                "high_risk",
                f"Patient risk score: {risk['score']}/100. {risk['reasoning']}",
                "high",
                doctor_id=doctor_id
            )
            alerts_created.append("high_risk")

        trends = self.health_agent.detect_behavioral_trends(patient_id)
        if trends["trend"] == "worsening":
            create_alert(
                patient_id,
                "worsening_condition",
                f"Patient messages indicate worsening condition. Signals: {', '.join(trends['signals'])}",
                "medium",
                doctor_id=doctor_id
            )
            alerts_created.append("worsening_condition")

        chat_analysis = self.conv_agent.analyze_chat_for_concerns(patient_id)
        if chat_analysis and chat_analysis.get("concern"):
            create_alert(
                patient_id,
                "patient_concern",
                f"AI detected patient concern: {chat_analysis.get('summary', 'Requires review')}",
                chat_analysis.get("severity", "medium"),
                doctor_id=doctor_id
            )
            alerts_created.append("patient_concern")

        adherence = self.health_agent.evaluate_adherence(patient_id)
        if not adherence["treatment_ongoing"] and adherence["completed_medications"] == 0:
            create_alert(
                patient_id,
                "no_prescription",
                "Patient has no active prescriptions assigned.",
                "low",
                doctor_id=doctor_id
            )
            alerts_created.append("no_prescription")

        return alerts_created

    def run_system_check(self):
        patients = get_all_patients()
        total_alerts = []
        for p in patients:
            alerts = self.check_and_alert(p["id"])
            total_alerts.extend(alerts)
        return total_alerts

    def get_active_alerts(self):
        return get_alerts(resolved=False)

    def dismiss_alert(self, alert_id):
        resolve_alert(alert_id)
