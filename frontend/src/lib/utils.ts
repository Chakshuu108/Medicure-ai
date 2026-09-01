import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const API_BASE = ''

const TOKEN_KEY = 'medicure_token'
const USER_KEY = 'medicure_user'

export interface User {
  role: string
  id: string
  name: string
  token: string
  hospital_id?: string
  patient_code?: string
  extra?: Record<string, unknown>
}

/** sessionStorage = each browser tab can hold a different login (doctor + patient side by side). */
export function saveAuth(user: User) {
  sessionStorage.setItem(TOKEN_KEY, user.token)
  sessionStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

export function getUser(): User | null {
  const raw = sessionStorage.getItem(USER_KEY)
  return raw ? JSON.parse(raw) : null
}

export function clearAuth() {
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(USER_KEY)
}

export interface AgentEvent {
  type: string
  agent: string
  status: 'running' | 'completed' | 'failed'
  detail?: string
  tool?: string
  next_agent?: string
  elapsed_seconds?: number
  timestamp: string
}

export const AGENT_LABELS: Record<string, string> = {
  orchestrator: 'Orchestrator',
  conversation_agent: 'Conversation Agent',
  risk_agent: 'Risk Assessment Agent',
  health_agent: 'Health Evaluation Agent',
  alerting_agent: 'Alerting Agent',
  scheduling_agent: 'Scheduling Agent',
  guardian_agent: 'Health Guardian',
  intelligence_agent: 'Health Intelligence Agent',
  synthesizer: 'Response Synthesizer',
}
