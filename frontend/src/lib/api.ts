import { getToken } from './utils'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${path}`, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = err.detail
    const message = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join(', ')
      : (typeof detail === 'string' ? detail : res.statusText || 'Request failed')
    throw new Error(message)
  }
  return res.json()
}

export const api = {
  getDemoCredentials: () => request<DemoCredential[]>('/api/demo-credentials'),
  loginAdmin: (email: string, password: string) =>
    request<AuthResponse>('/api/auth/admin/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  loginDoctor: (email: string, password: string) =>
    request<AuthResponse>('/api/auth/doctor/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  loginReceptionist: (email: string, password: string) =>
    request<AuthResponse>('/api/auth/receptionist/login', { method: 'POST', body: JSON.stringify({ email, password }) }),
  loginPatient: (patient_code: string) =>
    request<AuthResponse>('/api/auth/patient/login', { method: 'POST', body: JSON.stringify({ patient_code }) }),
  loginPatientGoogle: (patient_code: string, code: string) =>
    request<AuthResponse>('/api/auth/patient/google-login', {
      method: 'POST',
      body: JSON.stringify({ patient_code, code }),
    }),
  getMe: () => request<Record<string, unknown>>('/api/auth/me'),
  getPatients: () => request<Patient[]>('/api/patients'),
  getDoctors: (hospital_id?: string) =>
    request<Doctor[]>(`/api/doctors${hospital_id ? `?hospital_id=${hospital_id}` : ''}`),
  getAlerts: () => request<Alert[]>('/api/alerts'),
  resolveAlert: (id: string) => request(`/api/alerts/${id}/resolve`, { method: 'PATCH' }),
  getChatHistory: () => request<ChatMessage[]>('/api/patient/chat/history'),
  getPrescriptions: (patientId: string) => request<Prescription[]>(`/api/prescriptions/patient/${patientId}`),
  createPrescription: (data: unknown) =>
    request('/api/prescriptions', { method: 'POST', body: JSON.stringify(data) }),
  getAvailableSlots: (doctor_id?: string, slot_date?: string) => {
    const params = new URLSearchParams()
    if (doctor_id) params.set('doctor_id', doctor_id)
    if (slot_date) params.set('slot_date', slot_date)
    return request<OPDSlot[]>(`/api/opd/slots/available?${params}`)
  },
  bookSlot: (slot_id: string) =>
    request('/api/opd/book', { method: 'POST', body: JSON.stringify({ slot_id }) }),
  getBookings: () => request<Booking[]>('/api/opd/bookings'),
  createOPDSlots: (data: unknown) =>
    request('/api/opd/slots', { method: 'POST', body: JSON.stringify(data) }),
  getTodayMCQ: () => request<MCQData>('/api/mcq/today'),
  submitMCQ: (data: unknown) =>
    request('/api/mcq/submit', { method: 'POST', body: JSON.stringify(data) }),
  getMCQHistory: () => request<MCQHistory[]>('/api/mcq/history'),
  getMCQTrends: (days = 30) => request<TrendData>(`/api/mcq/trends?days=${days}`),
  patientSessionInit: (google_access_token?: string | null) =>
    request<SessionInitResult>('/api/patient/session-init', {
      method: 'POST',
      body: JSON.stringify({ google_access_token: google_access_token || null }),
    }),
  getGuardianLatest: () => request<GuardianResult>('/api/patient/guardian/latest'),
  runGuardianCheck: (force = false) =>
    request<GuardianResult>(`/api/patient/guardian-check?force=${force}`, { method: 'POST' }),
  getSchedulePreview: () => request<{ schedule: ScheduleItem[] }>('/api/patient/schedule/preview'),
  getGoogleAuthUrl: (purpose = 'patient_login') =>
    request<{ url: string }>(`/api/auth/google/url?purpose=${purpose}`),
  exchangeGoogleCode: (code: string) =>
    request<{ access_token: string; refresh_token?: string; expires_in?: number }>(
      '/api/auth/google/callback',
      { method: 'POST', body: JSON.stringify({ code }) },
    ),
  refreshGoogleToken: (refresh_token: string) =>
    request<{ access_token: string; expires_in?: number }>(
      '/api/auth/google/refresh',
      { method: 'POST', body: JSON.stringify({ refresh_token }) },
    ),
  syncToGoogleCalendar: () =>
    request<{ success: boolean; message: string; events_created?: number; errors?: string[] }>(
      '/api/patient/schedule/sync-calendar',
      { method: 'POST', body: JSON.stringify({}) },
    ),
  createMeetSummary: (booking_id: string, transcript: string) =>
    request<{ message: string; summary: Record<string, unknown> }>('/api/opd/meet-summary', {
      method: 'POST',
      body: JSON.stringify({ booking_id, transcript }),
    }),
  appendTranscriptLine: (booking_id: string, speaker_label: string, text: string, timestamp_ms = 0) =>
    request<{ ok: boolean }>('/api/opd/transcript-line', {
      method: 'POST',
      body: JSON.stringify({ booking_id, speaker_label, text, timestamp_ms }),
    }),
  getTranscript: (booking_id: string) =>
    request<{ lines: { speaker_label: string; text: string; timestamp_ms: number }[]; formatted: string; count: number }>(
      `/api/opd/transcript/${booking_id}`,
    ),
  getMeetSummary: (booking_id: string) =>
    request<{ summary: Record<string, unknown> | null; created_at?: string }>(`/api/opd/meet-summary/${booking_id}`),
  getMeetSummaries: () => request<MeetSummaryRecord[]>('/api/opd/meet-summaries'),
  getDoctorSlots: () => request<DoctorSlot[]>('/api/opd/slots/mine'),
  getCareAutopilot: () => request<CareAutopilotData>('/api/patient/care-autopilot'),
  getBookingLimit: () => request<BookingLimit>('/api/opd/booking-limit'),
  createPatient: (data: unknown) =>
    request('/api/admin/patients', { method: 'POST', body: JSON.stringify(data) }),
  createDoctor: (data: unknown) =>
    request('/api/admin/doctors', { method: 'POST', body: JSON.stringify(data) }),
  createReceptionist: (data: unknown) =>
    request('/api/admin/receptionists', { method: 'POST', body: JSON.stringify(data) }),
}

export interface AuthResponse {
  access_token: string
  role: string
  user_id: string
  name: string
  hospital_id?: string
  extra?: Record<string, unknown>
}

export interface DemoCredential {
  role: string
  email_or_code: string
  password: string | null
  description: string
}

export interface Patient {
  id: string
  patient_code: string
  name: string
  age: number
  gender: string
  disease: string
  risk_level: string
  risk_score: number
  visit_date: string
}

export interface Doctor {
  id: string
  name: string
  specialization: string
  hospital_id: string
}

export interface Alert {
  id: string
  patient_id: string
  patient_name?: string
  patient_code?: string
  alert_type: string
  alert_type_label?: string
  message: string
  summary?: string
  severity: string
  severity_label?: string
  resolved: boolean
  created_at: string
}

export interface ChatMessage {
  role: string
  content: string
  created_at: string
}

export interface Prescription {
  id: string
  doctor_notes: string
  created_at: string
  medicines: { name: string; dosage: string; timing: string; duration_days: number }[]
}

export interface OPDSlot {
  id: string
  doctor_id: string
  doctor_name: string
  slot_date: string
  start_time: string
  end_time: string
  room?: string
}

export interface DoctorSlot {
  id: string
  slot_date: string
  start_time: string
  end_time: string
  is_booked: boolean
  room: string
  booking_id?: string | null
  patient_name?: string | null
}

export interface BookingLimit {
  can_book: boolean
  active_booking: {
    id: string
    slot_date: string
    start_time: string
    room: string
  } | null
}

export interface CareAutopilotData {
  status: string
  patient_message: string
  priorities: string[]
  autonomous_actions: string[]
  trends?: TrendData
  alerts: Alert[]
  upcoming_meds: ScheduleItem[]
  bookings: { slot_date: string; start_time: string; room: string; status: string }[]
  proactive_monitor?: ProactiveMonitorInfo | null
  guardian?: GuardianResult
}

export interface Booking {
  id: string
  patient_name: string
  status: string
  slot_date: string
  start_time: string
  room: string
}

export interface MeetSummaryRecord {
  id: string
  booking_id: string
  patient_name: string
  slot_date: string
  start_time: string
  end_time: string
  summary_json: Record<string, unknown>
  created_at: string
}

export interface MCQData {
  questions: MCQQuestion[]
  date?: string
  cached?: boolean
}

export interface MCQOption {
  text: string
  score?: number
  tag?: string
}

export interface MCQQuestion {
  id: number
  question: string
  options: (string | MCQOption)[]
  category?: string
  type?: string
}

export interface MCQSubmitResult {
  message: string
  score: number
  status: string
  feedback?: { message: string; icon: string; color: string; action: string }
}

export interface TrendPoint {
  date: string
  total_score: number | null
  status: string
  missed: boolean
  rolling_avg: number | null
}

export interface TrendData {
  points: TrendPoint[]
  summary: {
    completed_days: number
    missed_days: number
    latest_status: string
    trend: string
  }
}

export interface GuardianFinding {
  type?: string
  title?: string
  description?: string
  reasoning_chain?: string[]
  severity: string
  action?: string
}

export interface GuardianResult {
  snapshot?: {
    checkin_count?: number
    days_silent?: number
    unresolved_alerts?: number
    disease?: string
    risk_level?: string
  }
  reasoning?: {
    findings?: GuardianFinding[]
    overall_assessment?: string
    patient_message?: string
    actions_taken_summary?: string
  }
  actions?: {
    action_log?: { action: string; finding: string; severity: string; timestamp?: string }[]
    alerts_sent?: number
    appointment_imminent?: boolean
  }
  trends?: TrendData
  ran_at?: string
  error?: string | null
  cached?: boolean
}

export interface ProactiveMonitorInfo {
  ran_at?: string
  duration_seconds?: number
  totals?: {
    patients_scanned?: number
    emails_sent?: number
    silence_alerts?: number
    guardian_alerts?: number
    errors?: number
  }
}

export interface SessionInitResult {
  guardian: GuardianResult
  reminders: { missed_dates: string[]; emails_sent: number; calendar_events: number; errors?: string[] }
  trends: TrendData
  proactive_monitor?: ProactiveMonitorInfo | null
}

export interface MCQHistory {
  date: string
  total_score: number
  status: string
}

export interface ScheduleItem {
  date: string
  time: string
  medicine: string
  dosage: string
  timing: string
}

export async function streamChat(
  message: string,
  onEvent: (event: Record<string, unknown>) => void,
): Promise<Record<string, unknown>> {
  const token = getToken()
  const res = await fetch('/api/patient/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  })

  if (!res.ok) throw new Error('Chat request failed')

  const reader = res.body?.getReader()
  const decoder = new TextDecoder()
  let result: Record<string, unknown> = {}

  if (!reader) throw new Error('No response stream')

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const chunk = decoder.decode(value)
    for (const line of chunk.split('\n')) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6).trim()
        if (data === '[DONE]') continue
        try {
          const event = JSON.parse(data)
          onEvent(event)
          if (event.type === 'chat_result') result = event.result
        } catch { /* skip */ }
      }
    }
  }
  return result
}

export function mcqOptionText(opt: string | MCQOption): string {
  return typeof opt === 'string' ? opt : opt.text
}
