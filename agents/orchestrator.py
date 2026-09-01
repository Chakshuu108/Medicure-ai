from agents.conversation_agent import ConversationAgent
from agents.agentic_ai import AgenticAI
from agents.risk_agent import RiskScoringAgent
from agents.health_agent import HealthEvaluationAgent
from agents.alerting_agent import AlertingAgent
from agents.scheduling_agent import SchedulingAgent
from agents.mcq_agent import MCQAgent
from agents.health_intelligence_agent import HealthIntelligenceAgent


class AgentOrchestrator:
    def __init__(self):
        self.conversation = ConversationAgent()
        self.agentic_ai   = AgenticAI()
        self.risk         = RiskScoringAgent()
        self.health       = HealthEvaluationAgent()
        self.alerting     = AlertingAgent()
        self.scheduling   = SchedulingAgent()
        self.mcq          = MCQAgent()
        self.intelligence = HealthIntelligenceAgent()

    def on_patient_message(self, patient_id: str, message: str,
                           use_agentic: bool = True,
                           session_state: dict | None = None) -> dict:
        """
        Route message through the autonomous agentic AI (default)
        or the legacy conversation agent.

        `session_state` is forwarded to AgenticAI so that partial slot
        information accumulates across Streamlit reruns (multi-turn booking).

        Returns:
          { reply, triage, action, success, confirmed, ... }
        """
        if use_agentic:
            result = self.agentic_ai.process(patient_id, message,
                                             session_state=session_state)
        else:
            result = self.conversation.chat(patient_id, message)

        # Always run the alerting check after any patient interaction
        self.alerting.check_and_alert(patient_id)
        return result

    def on_prescription_created(self, patient_id: str):
        self.risk.evaluate(patient_id)
        self.alerting.check_and_alert(patient_id)
        return self.scheduling.get_schedule_preview(patient_id)

    def on_patient_login(self, patient_id: str):
        return {
            "risk":      self.risk.evaluate(patient_id),
            "adherence": self.health.evaluate_adherence(patient_id),
            "trends":    self.health.detect_behavioral_trends(patient_id),
            "schedule":  self.scheduling.get_schedule_preview(patient_id),
        }

    def get_doctor_dashboard_data(self):
        return {"alerts": self.alerting.get_active_alerts()}

    def run_full_system_check(self):
        return self.alerting.run_system_check()
