import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class AgentEventEmitter:
    """Emits structured agent events for SSE streaming."""

    def __init__(self):
        self._queues: list[asyncio.Queue] = []
        self.events: list[dict] = []
        self.started_at = datetime.now(timezone.utc)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.append(q)
        return q

    async def emit(self, event_type: str, agent: str, **kwargs: Any) -> None:
        event = {
            "type": event_type,
            "agent": agent,
            "status": kwargs.get("status", "running"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **{k: v for k, v in kwargs.items() if k != "status"},
        }
        self.events.append(event)
        for q in self._queues:
            await q.put(event)
        logger.debug("Agent event: %s", json.dumps(event, default=str))

    async def emit_started(self, agent: str, detail: str = "") -> None:
        await self.emit("agent_started", agent, status="running", detail=detail)

    async def emit_thinking(self, agent: str, detail: str = "") -> None:
        await self.emit("agent_thinking", agent, status="running", detail=detail)

    async def emit_tool_called(self, agent: str, tool: str, **kwargs) -> None:
        await self.emit("tool_called", agent, status="running", tool=tool, **kwargs)

    async def emit_completed(self, agent: str, detail: str = "") -> None:
        await self.emit("agent_completed", agent, status="completed", detail=detail)

    async def emit_failed(self, agent: str, error: str) -> None:
        await self.emit("agent_failed", agent, status="failed", error=error)

    async def emit_routing(self, next_agent: str, reason: str = "") -> None:
        await self.emit("next_agent_selected", "orchestrator", status="running",
                        next_agent=next_agent, reason=reason)

    async def emit_final(self, message: str = "") -> None:
        elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        await self.emit("final_response", "orchestrator", status="completed",
                        message=message, elapsed_seconds=round(elapsed, 2))

    def elapsed_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()


async def run_with_events(
    emitter: AgentEventEmitter,
    agent_name: str,
    coro: Callable[[], Awaitable[Any]],
    thinking_msg: str = "Processing...",
) -> Any:
    await emitter.emit_started(agent_name)
    await emitter.emit_thinking(agent_name, thinking_msg)
    try:
        result = await coro()
        await emitter.emit_completed(agent_name)
        return result
    except Exception as exc:
        await emitter.emit_failed(agent_name, str(exc))
        raise
