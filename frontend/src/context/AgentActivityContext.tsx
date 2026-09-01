import { createContext, useContext, useState, useCallback, useRef, type ReactNode } from 'react'
import type { AgentEvent } from '../lib/utils'
import { AGENT_LABELS } from '../lib/utils'

interface AgentActivityState {
  events: AgentEvent[]
  isActive: boolean
  isExpanded: boolean
  isFirstTime: boolean
  elapsed: number
  agentsCount: number
  startActivity: () => void
  addEvent: (event: Record<string, unknown>) => void
  endActivity: () => void
  toggleExpanded: () => void
  clearEvents: () => void
}

const AgentActivityContext = createContext<AgentActivityState | null>(null)

export function AgentActivityProvider({ children }: { children: ReactNode }) {
  const [events, setEvents] = useState<AgentEvent[]>([])
  const [isActive, setIsActive] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [isFirstTime, setIsFirstTime] = useState(() => !sessionStorage.getItem('medicure_agent_seen'))
  const [elapsed, setElapsed] = useState(0)
  const startTimeRef = useRef(0)

  const startActivity = useCallback(() => {
    setEvents([])
    setIsActive(true)
    setIsExpanded(isFirstTime)
    startTimeRef.current = Date.now()
    setElapsed(0)
  }, [isFirstTime])

  const addEvent = useCallback((event: Record<string, unknown>) => {
    const agentEvent: AgentEvent = {
      type: event.type as string,
      agent: event.agent as string,
      status: (event.status as AgentEvent['status']) || 'running',
      detail: event.detail as string,
      tool: event.tool as string,
      next_agent: event.next_agent as string,
      elapsed_seconds: event.elapsed_seconds as number,
      timestamp: (event.timestamp as string) || new Date().toISOString(),
    }
    setEvents(prev => {
      const existing = prev.findIndex(e => e.agent === agentEvent.agent && e.type === agentEvent.type)
      if (existing >= 0 && agentEvent.type === 'agent_completed') {
        const updated = [...prev]
        updated[existing] = agentEvent
        return updated
      }
      if (prev.some(e => e.agent === agentEvent.agent && e.type === agentEvent.type)) return prev
      return [...prev, agentEvent]
    })
    if (typeof event.elapsed_seconds === 'number' && event.elapsed_seconds < 600) {
      setElapsed(event.elapsed_seconds)
    }
  }, [])

  const endActivity = useCallback(() => {
    setIsActive(false)
    if (startTimeRef.current > 0) {
      setElapsed((Date.now() - startTimeRef.current) / 1000)
    }
    if (isFirstTime) {
      sessionStorage.setItem('medicure_agent_seen', '1')
      setIsFirstTime(false)
    }
  }, [isFirstTime])

  const agentsCount = new Set(events.map(e => e.agent)).size

  return (
    <AgentActivityContext.Provider value={{
      events, isActive, isExpanded, isFirstTime, elapsed, agentsCount,
      startActivity, addEvent, endActivity,
      toggleExpanded: () => setIsExpanded(v => !v),
      clearEvents: () => setEvents([]),
    }}>
      {children}
    </AgentActivityContext.Provider>
  )
}

export function useAgentActivity() {
  const ctx = useContext(AgentActivityContext)
  if (!ctx) throw new Error('useAgentActivity must be used within AgentActivityProvider')
  return ctx
}

export { AGENT_LABELS }
