import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { motion } from 'framer-motion'
import { Button } from './ui/Button'
import { Card } from './ui/Card'
import { streamChat, api, type ChatMessage } from '../lib/api'
import { ChatMessageContent } from './ChatMessageContent'
import { useAgentActivity } from '../context/AgentActivityContext'

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const { startActivity, addEvent, endActivity } = useAgentActivity()

  useEffect(() => {
    api.getChatHistory().then(setMessages).catch(() => {})
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    if (!input.trim() || loading) return
    const msg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg, created_at: new Date().toISOString() }])
    setLoading(true)
    startActivity()

    try {
      const result = await streamChat(msg, addEvent)
      const reply = (result.reply as string) || (result.error as string) || 'I could not process your request.'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: reply,
        created_at: new Date().toISOString(),
      }])
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Connection error. Is the backend running on port 8000?'
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: errMsg,
        created_at: new Date().toISOString(),
      }])
    } finally {
      endActivity()
      setLoading(false)
    }
  }

  return (
    <Card title="AI Health Assistant" subtitle="Powered by LangGraph multi-agent orchestration">
      <div className="flex flex-col h-[500px]">
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.length === 0 && (
            <div className="text-center py-12 text-slate-400 dark:text-slate-500">
              <Bot className="w-12 h-12 mx-auto mb-3 opacity-40" />
              <p className="text-sm">Ask me about symptoms, medications, or book an appointment.</p>
              <div className="flex flex-wrap gap-2 justify-center mt-4">
                {['I have a headache', 'Book an appointment', 'Show my prescriptions', 'Check my alerts'].map(s => (
                  <button key={s} onClick={() => setInput(s)}
                    className="text-xs px-3 py-1.5 bg-primary-50 dark:bg-primary-950/50 text-primary-700 dark:text-primary-300 rounded-full hover:bg-primary-100 dark:hover:bg-primary-900/50 transition-colors">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                ${m.role === 'user' ? 'bg-primary-600' : 'bg-slate-100 dark:bg-slate-800'}`}>
                {m.role === 'user' ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-primary-600 dark:text-primary-400" />}
              </div>
              <div className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed
                ${m.role === 'user'
                  ? 'bg-primary-600 text-white rounded-tr-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 rounded-tl-sm'}`}>
                <ChatMessageContent content={m.content} isUser={m.role === 'user'} />
              </div>
            </motion.div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                <Bot className="w-4 h-4 text-primary-600 dark:text-primary-400" />
              </div>
              <div className="px-4 py-3 bg-slate-100 dark:bg-slate-800 rounded-2xl rounded-tl-sm">
                <div className="flex gap-1">
                  {[0, 1, 2].map(i => (
                    <div key={i} className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="flex gap-2 mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Describe symptoms, ask about meds, or book an appointment..."
            className="portal-input flex-1"
            disabled={loading}
          />
          <Button onClick={send} loading={loading} disabled={!input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </Card>
  )
}
