"""LangGraph state and multi-agent workflow."""

from __future__ import annotations

import json
import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.events import AgentEventEmitter
from app.agents.tools.patient_tools import create_tools
from app.config import get_settings, is_groq_configured

def _settings():
    return get_settings()


API_KEY_ERROR = (
    "AI service is not configured. Add your Groq API key to backend/.env:\n"
    "GROQ_API_KEY=gsk_your_actual_key_here\n"
    "Then restart the backend server."
)

AGENT_LABELS = {
    "orchestrator": "Orchestrator",
    "conversation_agent": "Conversation Agent",
    "risk_agent": "Risk Assessment Agent",
    "health_agent": "Health Evaluation Agent",
    "alerting_agent": "Alerting Agent",
    "scheduling_agent": "Scheduling Agent",
    "guardian_agent": "Health Guardian",
    "intelligence_agent": "Health Intelligence Agent",
    "synthesizer": "Response Synthesizer",
}


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    patient_id: str
    user_message: str
    next_agent: str
    agents_run: Annotated[list[str], operator.add]
    context: dict
    triage: str | None
    action_taken: str | None
    final_reply: str
    needs_risk: bool
    needs_health: bool
    needs_alerting: bool
    needs_guardian: bool
    needs_intelligence: bool
    workflow_type: str


def _get_llm():
    s = _settings()
    return ChatGroq(
        api_key=s.groq_api_key,
        model=s.groq_model,
        temperature=0.2,
        max_tokens=1200,
    )


def _extract_content(response) -> str:
    """Extract text from LLM response (handles str, list blocks, empty reasoning models)."""
    content = getattr(response, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text") or block.get("content") or "")
            elif hasattr(block, "text"):
                parts.append(getattr(block, "text", "") or "")
        joined = "".join(parts).strip()
        if joined:
            return joined
    return ""


def _emergency_reply(message: str) -> str | None:
    """Hardcoded urgent response when LLM fails on emergency keywords."""
    msg = message.lower()
    triggers = (
        "heart attack", "heart attac", "chest pain", "can't breathe", "cannot breathe",
        "stroke", "unconscious", "severe bleeding", "suicide", "overdose",
        "not breathing", "cardiac arrest",
    )
    if any(t in msg for t in triggers):
        return (
            "**This may be a medical emergency.**\n\n"
            "If you are experiencing chest pain, difficulty breathing, or signs of a heart attack:\n"
            "1. **Call emergency services immediately** (112 / 102 / 108 in India)\n"
            "2. **Do not drive yourself** — wait for an ambulance\n"
            "3. Stay calm, sit or lie down, and loosen tight clothing\n"
            "4. If your doctor has advised it and you are not allergic, aspirin may help while waiting\n\n"
            "I am an AI assistant and cannot provide emergency care. Please seek immediate medical attention now.\n\n"
            "TRIAGE_VERDICT: URGENT"
        )
    return None


def _simple_reply(message: str) -> str | None:
    """Fast local replies for greetings and very short messages."""
    msg = message.strip().lower()
    greetings = {
        "hi", "hlo", "hello", "hey", "hii", "hiii", "good morning",
        "good afternoon", "good evening", "namaste", "help",
    }
    if msg in greetings or (len(msg) <= 4 and msg.isalpha()):
        return (
            "Hello! I'm MediCure's AI health assistant. I can help you with:\n"
            "- Symptoms and health questions\n"
            "- Your medications and prescriptions\n"
            "- Booking or cancelling OPD appointments\n"
            "- Daily health check guidance\n\n"
            "How can I help you today?"
        )
    return None


def _clean_reply_for_user(text: str) -> str:
    for marker in ("\nTRIAGE_VERDICT:", "TRIAGE_VERDICT:"):
        if marker in text:
            text = text.split(marker)[0].strip()
    return text.strip()


def _ensure_reply(text: str, user_message: str) -> str:
    """Never return empty string to the user."""
    cleaned = _clean_reply_for_user(text or "")
    if cleaned:
        return cleaned
    return _emergency_reply(user_message) or _simple_reply(user_message) or (
        "I received your message but had trouble generating a full response. "
        "Please try again or rephrase your question."
    )


async def orchestrator_node(state: AgentState, emitter: AgentEventEmitter) -> dict:
    await emitter.emit_started("orchestrator", "Analyzing request and planning agent workflow")

    if not is_groq_configured():
        await emitter.emit_failed("orchestrator", "Groq API key not configured")
        return {
            "next_agent": "synthesizer",
            "final_reply": API_KEY_ERROR,
            "agents_run": ["orchestrator"],
            "needs_risk": False,
            "needs_health": False,
            "needs_alerting": False,
            "needs_guardian": False,
            "needs_intelligence": False,
        }

    msg = state["user_message"].lower()

    needs_risk = any(w in msg for w in [
        "pain", "symptom", "fever", "chest", "breath", "dizzy", "hurt", "sick", "worse",
        "headache", "heart", "attack", "emergency", "stroke", "unconscious",
    ])
    needs_health = any(w in msg for w in ["adherence", "missed", "medicine", "dose", "taking", "medication", "pill", "forgot"])
    needs_alerting = needs_risk  # only alert on symptom-related messages, skip extra health agent
    needs_guardian = state.get("workflow_type") == "guardian_check"
    needs_intelligence = state.get("workflow_type") == "health_analysis"
    needs_scheduling = any(w in msg for w in ["book", "appointment", "schedule", "slot", "cancel", "opd"])

    route = "conversation_agent"
    if needs_scheduling:
        route = "scheduling_agent"
    elif needs_guardian:
        route = "guardian_agent"
    elif needs_intelligence:
        route = "intelligence_agent"

    await emitter.emit_routing(route, f"Selected based on message intent analysis")
    await emitter.emit_completed("orchestrator")

    return {
        "next_agent": route,
        "needs_risk": needs_risk,
        "needs_health": needs_health,
        "needs_alerting": needs_alerting,
        "needs_guardian": needs_guardian,
        "needs_intelligence": needs_intelligence,
        "agents_run": ["orchestrator"],
    }


def route_from_orchestrator(state: AgentState) -> str:
    return state.get("next_agent", "conversation_agent")


async def conversation_node(state: AgentState, emitter: AgentEventEmitter, db: AsyncSession) -> dict:
    await emitter.emit_started("conversation_agent", "Processing patient message with context")

    quick = _simple_reply(state["user_message"])
    if quick:
        await emitter.emit_completed("conversation_agent")
        return {
            "messages": [AIMessage(content=quick)],
            "final_reply": quick,
            "agents_run": ["conversation_agent"],
            "next_agent": "synthesizer",
        }

    tools = create_tools(db, state["patient_id"])
    llm = _get_llm().bind_tools(tools)

    system = SystemMessage(content="""You are MediCure's autonomous healthcare assistant.
You help patients with health questions, medication queries, and general wellness.
Use tools when you need patient data. Be empathetic and precise.
For symptoms, assess urgency and mention if they should seek immediate care.
Always remind patients this is informational, not a diagnosis.""")
    messages = [system] + state["messages"] + [HumanMessage(content=state["user_message"])]

    await emitter.emit_thinking("conversation_agent", "Generating contextual response")
    try:
        response = await llm.ainvoke(messages)
    except Exception as exc:
        await emitter.emit_failed("conversation_agent", str(exc))
        err = API_KEY_ERROR if "401" in str(exc) or "invalid_api_key" in str(exc).lower() else f"AI error: {exc}"
        return {
            "messages": [AIMessage(content=err)],
            "final_reply": err,
            "agents_run": ["conversation_agent"],
            "next_agent": "synthesizer",
        }

    tool_results = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_node = ToolNode(tools)
        for tc in response.tool_calls:
            await emitter.emit_tool_called("conversation_agent", tc["name"])
        tool_result = await tool_node.ainvoke({"messages": [response]})
        tool_results = tool_result.get("messages", [])
        follow_up = await llm.ainvoke([system] + messages + [response] + tool_results)
        final_text = _extract_content(follow_up) or _extract_content(response)
    else:
        final_text = _extract_content(response)

    if not final_text.strip():
        fallback = await _get_llm().ainvoke([
            system,
            HumanMessage(content=state["user_message"]),
        ])
        final_text = _extract_content(fallback)

    final_text = _ensure_reply(final_text, state["user_message"])

    triage = None
    if "TRIAGE_VERDICT: URGENT" in final_text:
        triage = "URGENT"
    elif "TRIAGE_VERDICT: MODERATE" in final_text:
        triage = "MODERATE"
    elif "TRIAGE_VERDICT: MILD" in final_text:
        triage = "MILD"

    await emitter.emit_completed("conversation_agent")
    return {
        "messages": [AIMessage(content=final_text)],
        "final_reply": final_text,
        "triage": triage,
        "agents_run": ["conversation_agent"],
        "next_agent": "risk_agent" if state.get("needs_risk") else "synthesizer",
    }


async def risk_node(state: AgentState, emitter: AgentEventEmitter, db: AsyncSession) -> dict:
    await emitter.emit_started("risk_agent", "Evaluating clinical risk factors")
    tools = create_tools(db, state["patient_id"])
    llm = _get_llm().bind_tools([tools[0], tools[1], tools[2], tools[8]])  # context, rx, chat, update_risk

    prompt = f"""Evaluate health risk for this patient based on their message: "{state['user_message']}"
Use tools to get context. Then call update_risk_score with appropriate score and reasoning.
Respond with a brief risk assessment summary."""

    await emitter.emit_thinking("risk_agent", "Analyzing symptoms and history")
    response = await llm.ainvoke([HumanMessage(content=prompt)])

    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_node = ToolNode([tools[0], tools[1], tools[2], tools[8]])
        for tc in response.tool_calls:
            await emitter.emit_tool_called("risk_agent", tc["name"])
        await tool_node.ainvoke({"messages": [response]})

    summary = f"Risk assessment completed. {response.content[:300]}"
    await emitter.emit_completed("risk_agent")
    return {
        "messages": [AIMessage(content=summary)],
        "agents_run": ["risk_agent"],
        "next_agent": "health_agent" if state.get("needs_health") else "alerting_agent" if state.get("needs_alerting") else "synthesizer",
    }


async def health_node(state: AgentState, emitter: AgentEventEmitter, db: AsyncSession) -> dict:
    await emitter.emit_started("health_agent", "Evaluating adherence and behavioral trends")
    tools = create_tools(db, state["patient_id"])
    llm = _get_llm().bind_tools([tools[0], tools[1], tools[2]])

    prompt = f"""Analyze medication adherence and health trends for patient.
Patient message: "{state['user_message']}"
Use tools for context. Provide adherence assessment and behavioral insights."""

    await emitter.emit_thinking("health_agent", "Checking medication patterns")
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_node = ToolNode([tools[0], tools[1], tools[2]])
        for tc in response.tool_calls:
            await emitter.emit_tool_called("health_agent", tc["name"])
        await tool_node.ainvoke({"messages": [response]})

    await emitter.emit_completed("health_agent")
    return {
        "messages": [AIMessage(content=f"Health evaluation: {response.content[:300]}")],
        "agents_run": ["health_agent"],
        "next_agent": "alerting_agent" if state.get("needs_alerting") else "synthesizer",
    }


async def alerting_node(state: AgentState, emitter: AgentEventEmitter, db: AsyncSession) -> dict:
    await emitter.emit_started("alerting_agent", "Checking alert conditions")
    tools = create_tools(db, state["patient_id"])
    create_alert_tool = tools[7]

    triage = state.get("triage")
    alert_created = False

    from app.services.alert_service import classify_chat_urgency, create_chat_symptom_alert

    urgency = classify_chat_urgency(state["user_message"])
    if urgency:
        await create_chat_symptom_alert(
            db,
            patient_id=state["patient_id"],
            message=state["user_message"],
        )
        alert_created = True
        triage = urgency.get("triage") or triage
        await emitter.emit_tool_called("alerting_agent", "create_alert")
    elif triage == "URGENT":
        await create_alert_tool.ainvoke({
            "alert_type": "emergency",
            "message": f"Urgent symptoms reported: {state['user_message'][:300]}",
            "severity": "severe",
        })
        alert_created = True
        await emitter.emit_tool_called("alerting_agent", "create_alert")

    if alert_created:
        await emitter.emit_completed("alerting_agent", f"Doctor notified ({urgency['severity'] if urgency else 'severe'})")
    else:
        llm = _get_llm().bind_tools([tools[3], create_alert_tool])
        prompt = f"""Review patient message: "{state['user_message']}"
If clinically concerning, call create_alert with plain English message and severity (low/medium/high/severe)."""
        await emitter.emit_thinking("alerting_agent", "Evaluating alert triggers")
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_node = ToolNode([tools[3], create_alert_tool])
            for tc in response.tool_calls:
                await emitter.emit_tool_called("alerting_agent", tc["name"])
            await tool_node.ainvoke({"messages": [response]})
            alert_created = True
            await emitter.emit_completed("alerting_agent", "Doctor notified")
        else:
            await emitter.emit_completed("alerting_agent", "No new alerts needed")

    return {
        "messages": [AIMessage(content="Your doctor has been notified." if alert_created else "Alert check complete.")],
        "agents_run": ["alerting_agent"],
        "next_agent": "synthesizer",
        "triage": triage,
    }


async def scheduling_node(state: AgentState, emitter: AgentEventEmitter, db: AsyncSession) -> dict:
    await emitter.emit_started("scheduling_agent", "Processing appointment request")
    from sqlalchemy import select
    from app.models import Doctor
    from app.services.opd_booking_service import (
        format_slots_for_chat,
        get_patient_active_booking,
        list_available_slots,
        patient_can_book,
        smart_book_from_context,
        smart_cancel_from_context,
    )

    cancel_reply = await smart_cancel_from_context(
        db,
        patient_id=state["patient_id"],
        user_message=state["user_message"],
    )
    if cancel_reply:
        await emitter.emit_completed("scheduling_agent", "Appointment cancelled")
        return {
            "messages": [AIMessage(content=cancel_reply)],
            "final_reply": cancel_reply,
            "action_taken": "cancelled",
            "agents_run": ["scheduling_agent"],
            "next_agent": "synthesizer",
        }

    booked_reply = await smart_book_from_context(
        db,
        patient_id=state["patient_id"],
        user_message=state["user_message"],
        messages=state.get("messages", []),
    )
    if booked_reply:
        await emitter.emit_completed("scheduling_agent", "Appointment booked")
        return {
            "messages": [AIMessage(content=booked_reply)],
            "final_reply": booked_reply,
            "action_taken": "booked",
            "agents_run": ["scheduling_agent"],
            "next_agent": "synthesizer",
        }

    msg = state["user_message"].lower()
    if any(w in msg for w in ["slot", "appointment", "opd", "available", "book", "schedule"]):
        if not await patient_can_book(db, state["patient_id"]):
            active = await get_patient_active_booking(db, state["patient_id"])
            slot = active.slot if active else None
            when = f"{slot.slot_date} at {slot.start_time}" if slot else "already booked"
            reply = (
                f"You already have an active appointment on **{when}**.\n\n"
                "Only **one OPD slot** is allowed per patient. "
                "Cancel your current booking before reserving another."
            )
        else:
            slots = await list_available_slots(db)
            doc_result = await db.execute(select(Doctor))
            doctors = {d.id: d.name for d in doc_result.scalars().all()}
            reply = format_slots_for_chat(slots, doctors)
        await emitter.emit_completed("scheduling_agent")
        return {
            "messages": [AIMessage(content=reply)],
            "final_reply": reply,
            "action_taken": "none",
            "agents_run": ["scheduling_agent"],
            "next_agent": "synthesizer",
        }

    tools = create_tools(db, state["patient_id"])
    sched_tools = [tools[4], tools[5], tools[6]]
    llm = _get_llm().bind_tools(sched_tools)
    history = state.get("messages", [])[-8:]
    prompt = HumanMessage(content=(
        f'Help with appointment scheduling. Patient says: "{state["user_message"]}"\n'
        "Use book_appointment with a slot_id when they choose a slot. "
        "Reply in short plain English with line breaks, not markdown tables."
    ))

    await emitter.emit_thinking("scheduling_agent", "Searching available slots")
    response = await llm.ainvoke([*history, prompt])

    action = "none"
    final_text = _extract_content(response)
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_node = ToolNode(sched_tools)
        for tc in response.tool_calls:
            await emitter.emit_tool_called("scheduling_agent", tc["name"])
            if tc["name"] == "book_appointment":
                action = "booked"
            elif tc["name"] == "cancel_appointment":
                action = "cancelled"
        tool_results = await tool_node.ainvoke({"messages": [response]})
        follow_up = await llm.ainvoke([*history, prompt, response, *tool_results.get("messages", [])])
        final_text = _extract_content(follow_up) or final_text

    await emitter.emit_completed("scheduling_agent")
    return {
        "messages": [AIMessage(content=final_text)],
        "final_reply": _ensure_reply(final_text, state["user_message"]),
        "action_taken": action,
        "agents_run": ["scheduling_agent"],
        "next_agent": "synthesizer",
    }


async def guardian_node(state: AgentState, emitter: AgentEventEmitter, db: AsyncSession) -> dict:
    await emitter.emit_started("guardian_agent", "Cross-session health pattern analysis")
    from sqlalchemy import select
    from app.models import MCQResponse, Patient

    result = await db.execute(select(Patient).where(Patient.id == state["patient_id"]))
    patient = result.scalar_one_or_none()
    mcq_result = await db.execute(
        select(MCQResponse)
        .where(MCQResponse.patient_id == state["patient_id"])
        .order_by(MCQResponse.date.desc())
        .limit(14)
    )
    mcqs = mcq_result.scalars().all()
    scores = [m.total_score for m in reversed(mcqs)]
    statuses = [m.status for m in reversed(mcqs)]

    llm = _get_llm()
    await emitter.emit_thinking("guardian_agent", "Detecting cross-session patterns")
    prompt = f"""You are Health Guardian — autonomous monitoring agent.
Patient: {patient.name if patient else 'Unknown'}, Condition: {patient.disease if patient else ''}
Recent scores: {scores}, Statuses: {statuses}
Detect patterns (day-of-week drops, worsening trends, missed check-ins).
Respond JSON: {{"findings": [{{"title": "", "description": "", "severity": "low|medium|high", "action": "alert_doctor|monitor|none"}}], "patient_message": "", "overall_assessment": ""}}"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    try:
        data = json.loads(response.content.replace("```json", "").replace("```", "").strip())
    except json.JSONDecodeError:
        data = {"findings": [], "patient_message": "Health data reviewed.", "overall_assessment": "Stable"}

    tools = create_tools(db, state["patient_id"])
    for finding in data.get("findings", []):
        if finding.get("action") == "alert_doctor" and finding.get("severity") in ("medium", "high"):
            await tools[7].ainvoke({
                "alert_type": "Health Guardian — Pattern Detected",
                "message": f"{finding.get('title')}: {finding.get('description')}",
                "severity": finding.get("severity", "medium"),
            })
            await emitter.emit_tool_called("guardian_agent", "create_alert")
            break

    reply = data.get("patient_message") or data.get("overall_assessment", "Health Guardian review complete.")
    await emitter.emit_completed("guardian_agent")
    return {
        "messages": [AIMessage(content=reply)],
        "final_reply": reply,
        "agents_run": ["guardian_agent"],
        "next_agent": "synthesizer",
    }


async def intelligence_node(state: AgentState, emitter: AgentEventEmitter, db: AsyncSession) -> dict:
    await emitter.emit_started("intelligence_agent", "ML risk prediction and clinical narrative")
    from sqlalchemy import select
    from app.models import MCQResponse, Patient, Alert

    result = await db.execute(select(Patient).where(Patient.id == state["patient_id"]))
    patient = result.scalar_one_or_none()
    mcq_result = await db.execute(
        select(MCQResponse).where(MCQResponse.patient_id == state["patient_id"]).limit(20)
    )
    mcqs = mcq_result.scalars().all()
    alert_result = await db.execute(
        select(Alert).where(Alert.patient_id == state["patient_id"], Alert.resolved == False)
    )
    alerts = alert_result.scalars().all()

    avg_score = sum(m.total_score for m in mcqs) / len(mcqs) if mcqs else 0
    risk_pred = "high" if avg_score < -3 or patient.risk_score > 70 else "medium" if avg_score < 0 else "low"

    await emitter.emit_thinking("intelligence_agent", "Generating clinical narrative")
    llm = _get_llm()
    prompt = f"""Generate clinical intelligence brief for doctor.
Patient: {patient.name}, Risk: {patient.risk_level} ({patient.risk_score}), Predicted: {risk_pred}
MCQ avg score: {avg_score:.1f}, Active alerts: {len(alerts)}
Provide: trajectory assessment, key concerns, recommended actions."""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    await emitter.emit_completed("intelligence_agent")
    return {
        "messages": [AIMessage(content=response.content)],
        "final_reply": response.content,
        "agents_run": ["intelligence_agent"],
        "next_agent": "synthesizer",
    }


async def synthesizer_node(state: AgentState, emitter: AgentEventEmitter) -> dict:
    await emitter.emit_started("synthesizer", "Combining agent outputs into final response")
    reply = (state.get("final_reply") or "").strip()
    if not reply:
        agent_msgs = []
        for m in state["messages"]:
            if isinstance(m, AIMessage):
                text = m.content if isinstance(m.content, str) else str(m.content or "")
                if text.strip():
                    agent_msgs.append(text.strip())
        reply = agent_msgs[-1] if agent_msgs else ""

    reply = _ensure_reply(reply, state.get("user_message", ""))

    agents_count = len(set(state.get("agents_run", [])))
    await emitter.emit_completed("synthesizer")
    await emitter.emit_final(f"Analysis complete — {agents_count} agents participated")
    return {"final_reply": reply, "agents_run": ["synthesizer"]}


def route_after_agent(state: AgentState) -> str:
    nxt = state.get("next_agent", "synthesizer")
    if nxt == "synthesizer":
        return "synthesizer"
    return nxt


def build_workflow(db: AsyncSession, emitter: AgentEventEmitter):
    """Build LangGraph workflow with event emission."""

    graph = StateGraph(AgentState)

    async def _orchestrator(s): return await orchestrator_node(s, emitter)
    async def _conversation(s): return await conversation_node(s, emitter, db)
    async def _risk(s): return await risk_node(s, emitter, db)
    async def _health(s): return await health_node(s, emitter, db)
    async def _alerting(s): return await alerting_node(s, emitter, db)
    async def _scheduling(s): return await scheduling_node(s, emitter, db)
    async def _guardian(s): return await guardian_node(s, emitter, db)
    async def _intelligence(s): return await intelligence_node(s, emitter, db)
    async def _synthesizer(s): return await synthesizer_node(s, emitter)

    graph.add_node("orchestrator", _orchestrator)
    graph.add_node("conversation_agent", _conversation)
    graph.add_node("risk_agent", _risk)
    graph.add_node("health_agent", _health)
    graph.add_node("alerting_agent", _alerting)
    graph.add_node("scheduling_agent", _scheduling)
    graph.add_node("guardian_agent", _guardian)
    graph.add_node("intelligence_agent", _intelligence)
    graph.add_node("synthesizer", _synthesizer)

    graph.set_entry_point("orchestrator")
    graph.add_conditional_edges("orchestrator", route_from_orchestrator)

    for agent in ["conversation_agent", "risk_agent", "health_agent", "alerting_agent",
                  "scheduling_agent", "guardian_agent", "intelligence_agent"]:
        graph.add_conditional_edges(agent, route_after_agent)

    graph.add_edge("synthesizer", END)
    return graph.compile()


