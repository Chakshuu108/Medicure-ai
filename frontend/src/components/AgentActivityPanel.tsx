import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp, Brain, CheckCircle2, Loader2, XCircle, Zap } from 'lucide-react'
import { useAgentActivity, AGENT_LABELS } from '../context/AgentActivityContext'

const STATUS_ICON = {
  running: <Loader2 className="w-3.5 h-3.5 animate-spin text-primary-500" />,
  completed: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />,
  failed: <XCircle className="w-3.5 h-3.5 text-red-500" />,
}

export function AgentActivityPanel() {
  const { events, isActive, isExpanded, isFirstTime, elapsed, agentsCount, toggleExpanded } = useAgentActivity()

  const uniqueAgents = Array.from(new Map(
    events.filter(e => e.type.includes('agent_')).map(e => [e.agent, e])
  ).values())

  const completedCount = uniqueAgents.filter(a => a.status === 'completed').length

  if (!isActive && events.length === 0) return null

  return (
    <div className="fixed right-4 bottom-4 z-50 w-72">
      <AnimatePresence>
        {(isActive || events.length > 0) && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-700 overflow-hidden"
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-primary-600 to-primary-700 cursor-pointer"
              onClick={toggleExpanded}
            >
              <div className="flex items-center gap-2 text-white">
                <Brain className="w-4 h-4" />
                <span className="text-sm font-semibold">AI Processing</span>
                {isActive && <Loader2 className="w-3 h-3 animate-spin text-primary-200" />}
              </div>
              <div className="flex items-center gap-2 text-primary-200 text-xs">
                {!isExpanded && !isActive && (
                  <span className="text-white font-medium">
                    ✓ {agentsCount} agents · {elapsed.toFixed(1)}s
                  </span>
                )}
                {isExpanded ? <ChevronDown className="w-4 h-4 text-white" /> : <ChevronUp className="w-4 h-4 text-white" />}
              </div>
            </div>

            {/* Agent list */}
            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: 'auto' }}
                  exit={{ height: 0 }}
                  className="overflow-hidden"
                >
                  {isFirstTime && (
                    <div className="px-4 py-2 bg-primary-50 dark:bg-primary-950/40 border-b border-primary-100 dark:border-primary-900">
                      <p className="text-xs text-primary-700 dark:text-primary-300">
                        <Zap className="w-3 h-3 inline mr-1" />
                        Watch our AI agents collaborate in real-time to process your request.
                      </p>
                    </div>
                  )}

                  <div className="px-4 py-3 space-y-2 max-h-64 overflow-y-auto">
                    {uniqueAgents.length === 0 && isActive && (
                      <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Initializing agents...
                      </div>
                    )}
                    {uniqueAgents.map((event, i) => (
                      <motion.div
                        key={event.agent}
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="flex items-start gap-2"
                      >
                        <div className="mt-0.5">{STATUS_ICON[event.status] || STATUS_ICON.running}</div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-slate-800 dark:text-slate-200">
                            {AGENT_LABELS[event.agent] || event.agent}
                          </p>
                          {event.detail && (
                            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">{event.detail}</p>
                          )}
                          {event.tool && (
                            <p className="text-xs text-primary-600">Tool: {event.tool}</p>
                          )}
                        </div>
                      </motion.div>
                    ))}

                    {/* Tool call events */}
                    {events.filter(e => e.type === 'tool_called').map((e, i) => (
                      <div key={`tool-${i}`} className="flex items-center gap-2 pl-5">
                        <span className="text-xs text-slate-400">↳</span>
                        <span className="text-xs text-primary-600">{e.tool}</span>
                      </div>
                    ))}
                  </div>

                  <div className="px-4 py-2 border-t border-slate-100 dark:border-slate-800 flex justify-between text-xs text-slate-500 dark:text-slate-400">
                    <span>{completedCount}/{uniqueAgents.length || '?'} agents</span>
                    <span>{elapsed > 0 ? `${elapsed.toFixed(1)}s` : '...'}</span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Collapsed summary */}
            {!isExpanded && !isActive && events.length > 0 && (
              <div className="px-4 py-2 text-xs text-slate-600 dark:text-slate-300 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                AI analysis completed · {agentsCount} agents · {elapsed.toFixed(1)}s
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
