"""Agent workflow runner service."""

from datetime import datetime, timezone

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.events import AgentEventEmitter
from app.agents.graph.workflow import AGENT_LABELS, API_KEY_ERROR, build_workflow, _ensure_reply
from app.models import AgentMemory, AgentRun, ChatMessage


class AgentWorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_chat(
        self,
        patient_id: str,
        message: str,
        emitter: AgentEventEmitter,
        workflow_type: str = "chat",
    ) -> dict:
        run = AgentRun(
            patient_id=patient_id,
            workflow_type=workflow_type,
            status="running",
            events=[],
        )
        self.db.add(run)
        await self.db.flush()

        # Load chat history into state
        from sqlalchemy import select
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.patient_id == patient_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(20)
        )
        history = list(reversed(result.scalars().all()))
        messages = []
        for h in history:
            if h.role == "user":
                messages.append(HumanMessage(content=h.content))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=h.content))

        workflow = build_workflow(self.db, emitter)
        initial_state = {
            "messages": messages,
            "patient_id": patient_id,
            "user_message": message,
            "next_agent": "orchestrator",
            "agents_run": [],
            "context": {},
            "triage": None,
            "action_taken": None,
            "final_reply": "",
            "needs_risk": False,
            "needs_health": False,
            "needs_alerting": False,
            "needs_guardian": False,
            "needs_intelligence": False,
            "workflow_type": workflow_type,
        }

        try:
            final_state = await workflow.ainvoke(initial_state)
            reply = _ensure_reply(
                final_state.get("final_reply", ""),
                message,
            )

            # Persist chat
            self.db.add(ChatMessage(patient_id=patient_id, role="user", content=message))
            self.db.add(ChatMessage(patient_id=patient_id, role="assistant", content=reply))

            if not reply.startswith("AI service is not configured"):
                self.db.add(AgentMemory(
                    patient_id=patient_id,
                    memory_type="episodic",
                    content=f"User: {message[:200]} | Reply: {reply[:200]}",
                    metadata_json={"agents": final_state.get("agents_run", []), "triage": final_state.get("triage")},
                ))

            run.status = "completed"
            run.events = emitter.events
            run.result = {
                "reply": reply,
                "triage": final_state.get("triage"),
                "action_taken": final_state.get("action_taken"),
                "agents_run": list(set(final_state.get("agents_run", []))),
                "agent_labels": [AGENT_LABELS.get(a, a) for a in set(final_state.get("agents_run", []))],
            }
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            await emitter.emit_final("Response ready")
            return run.result
        except Exception as exc:
            err_msg = (
                API_KEY_ERROR if "401" in str(exc) or "invalid_api_key" in str(exc).lower()
                else f"Sorry, something went wrong: {exc}"
            )
            await emitter.emit_failed("orchestrator", str(exc))
            await emitter.emit_final("Workflow failed")

            self.db.add(ChatMessage(patient_id=patient_id, role="user", content=message))
            self.db.add(ChatMessage(patient_id=patient_id, role="assistant", content=err_msg))

            run.status = "failed"
            run.events = emitter.events
            run.result = {"reply": err_msg, "error": str(exc), "agents_run": []}
            run.completed_at = datetime.now(timezone.utc)
            await self.db.flush()
            return run.result

    async def run_guardian_check(self, patient_id: str, emitter: AgentEventEmitter) -> dict:
        return await self.run_chat(patient_id, "Run health guardian analysis", emitter, workflow_type="guardian_check")

    async def run_health_analysis(self, patient_id: str, emitter: AgentEventEmitter) -> dict:
        return await self.run_chat(patient_id, "Generate health intelligence analysis", emitter, workflow_type="health_analysis")
