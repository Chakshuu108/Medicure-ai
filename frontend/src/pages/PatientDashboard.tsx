import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { DashboardLayout, PatientTabs } from '../components/Layout'
import { ChatPanel } from '../components/ChatPanel'
import { CarePlanPanel } from '../components/CarePlanPanel'
import { HealthGuardianPanel } from '../components/HealthGuardianPanel'
import { HealthTrendChart } from '../components/HealthTrendChart'
import { VideoCallPanel } from '../components/VideoCallPanel'
import { ConsultationSummariesPanel } from '../components/ConsultationSummariesPanel'
import { AlertsList } from '../components/AlertsList'
import { Card, Badge } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { useAuth } from '../context/AuthContext'
import {
  api,
  mcqOptionText,
  type Prescription,
  type OPDSlot,
  type Booking,
  type Alert,
  type MCQData,
  type MCQSubmitResult,
  type TrendData,
} from '../lib/api'

export function PatientDashboard() {
  const [searchParams] = useSearchParams()
  const [tab, setTab] = useState(() => searchParams.get('tab') || 'chat')
  const { user } = useAuth()
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [slots, setSlots] = useState<OPDSlot[]>([])
  const [bookings, setBookings] = useState<Booking[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [mcq, setMcq] = useState<MCQData | null>(null)
  const [mcqAnswers, setMcqAnswers] = useState<Record<number, number>>({})
  const [mcqSubmitted, setMcqSubmitted] = useState(false)
  const [mcqFeedback, setMcqFeedback] = useState<MCQSubmitResult | null>(null)
  const [trends, setTrends] = useState<TrendData | null>(null)
  const [sessionNote, setSessionNote] = useState('')
  const [canBookSlot, setCanBookSlot] = useState(true)

  useEffect(() => {
    if (!user || user.role !== 'patient') return
    api.patientSessionInit()
      .then(res => {
        setTrends(res.trends)
        const r = res.reminders
        if (r.missed_dates.length > 0) {
          const parts = []
          if (r.emails_sent) parts.push(`${r.emails_sent} email reminder(s) sent`)
          if (r.calendar_events) parts.push(`${r.calendar_events} calendar reminder(s) added`)
          setSessionNote(parts.length ? parts.join(' · ') : `You have ${r.missed_dates.length} missed check-in day(s).`)
        }
      })
      .catch(() => {})
  }, [user])

  const reloadPrescriptions = () => {
    if (user) api.getPrescriptions(user.id).then(setPrescriptions).catch(() => {})
  }

  useEffect(() => {
    if (tab === 'care' && user) reloadPrescriptions()
    if (tab === 'opd') {
      api.getAvailableSlots().then(setSlots).catch(() => {})
      api.getBookings().then(setBookings).catch(() => {})
      api.getBookingLimit().then(r => setCanBookSlot(r.can_book)).catch(() => setCanBookSlot(true))
    }
    if (tab === 'alerts') api.getAlerts().then(setAlerts).catch(() => {})
    if (tab === 'health') {
      api.getTodayMCQ().then(setMcq).catch(() => {})
      api.getMCQTrends(14).then(data => {
        setTrends(data)
        const today = new Date().toISOString().slice(0, 10)
        const todayPoint = data.points.find(p => p.date === today)
        if (todayPoint && !todayPoint.missed) setMcqSubmitted(true)
      }).catch(() => {})
    }
  }, [tab, user])

  const bookSlot = async (slotId: string) => {
    if (!canBookSlot) {
      alert('You already have an active appointment. Only one OPD slot is allowed at a time.')
      return
    }
    try {
      await api.bookSlot(slotId)
      api.getBookings().then(setBookings)
      api.getAvailableSlots().then(setSlots)
      api.getBookingLimit().then(r => setCanBookSlot(r.can_book))
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Could not book slot')
    }
  }

  const submitMCQ = async () => {
    if (!mcq) return
    const responses: Record<string, number> = {}
    for (const [k, v] of Object.entries(mcqAnswers)) responses[String(k)] = v
    const result = await api.submitMCQ({
      responses,
      total_score: 0,
      status: 'Stable',
      side_effects: [],
      adherence_status: '',
    }) as MCQSubmitResult
    setMcqFeedback(result)
    setMcqSubmitted(true)
    api.getMCQTrends(14).then(setTrends)
  }

  return (
    <DashboardLayout title="Patient Portal" tabs={PatientTabs} activeTab={tab} onTabChange={setTab}>
      {sessionNote && (
        <div className="portal-banner-warning mb-4">
          {sessionNote}
        </div>
      )}

      {tab === 'chat' && <ChatPanel />}
      {tab === 'care' && <CarePlanPanel prescriptions={prescriptions} onPrescriptionsChange={reloadPrescriptions} />}

      {tab === 'health' && (
        <div className="space-y-6">
          <Card title="Daily Health Check" subtitle="AI questions tailored to your condition and medications">
            {!mcqSubmitted ? (
              <div className="space-y-6">
                {mcq?.questions.map(q => (
                  <div key={q.id}>
                    <p className="font-medium text-slate-800 dark:text-slate-200 mb-3">{q.question}</p>
                    <div className="grid sm:grid-cols-1 gap-2">
                      {q.options.map((opt, i) => (
                        <button
                          key={i}
                          type="button"
                          onClick={() => setMcqAnswers(prev => ({ ...prev, [q.id]: i }))}
                          className={`px-4 py-2.5 rounded-xl text-sm border transition-all text-left
                            ${mcqAnswers[q.id] === i
                              ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/40 text-primary-700 dark:text-primary-300'
                              : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500 dark:text-slate-200'}`}
                        >
                          {mcqOptionText(opt)}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
                <Button onClick={submitMCQ} disabled={Object.keys(mcqAnswers).length < (mcq?.questions.length || 5)}>
                  Submit Health Check
                </Button>
              </div>
            ) : (
              <div className="text-center py-6">
                <div className="text-4xl mb-2">{mcqFeedback?.feedback?.icon || '✅'}</div>
                <p className="font-semibold text-slate-800 dark:text-slate-200">{mcqFeedback?.feedback?.message || 'Health check submitted!'}</p>
                {mcqFeedback && (
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                    Score: {mcqFeedback.score} · Status: {mcqFeedback.status}
                  </p>
                )}
              </div>
            )}
          </Card>

          {trends && (
            <Card title="Health Trend Chart" subtitle="Date-wise line chart — missed days labelled, no score line">
              <HealthTrendChart points={trends.points} />
            </Card>
          )}
        </div>
      )}

      {tab === 'alerts' && (
        <AlertsList alerts={alerts} role="patient" />
      )}

      {tab === 'opd' && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card title="Available Slots" subtitle={canBookSlot ? 'One appointment per patient' : undefined}>
            {!canBookSlot && (
              <div className="mb-3 portal-banner-warning text-amber-900 dark:text-amber-200">
                You already have an active booking. Cancel it before booking another slot.
              </div>
            )}
            <div className="space-y-2">
              {slots.length === 0 ? <p className="text-slate-500 dark:text-slate-400 text-sm">No slots available.</p> :
                slots.map(s => (
                  <div key={s.id} className="flex items-center justify-between p-3 portal-surface rounded-xl">
                    <div>
                      <p className="font-medium text-sm">Dr. {s.doctor_name}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{s.slot_date} · {s.start_time}{s.end_time ? ` – ${s.end_time}` : ''}</p>
                      {s.room && <p className="text-xs text-primary-600 dark:text-primary-400 mt-0.5">Room: {s.room}</p>}
                    </div>
                    <Button size="sm" onClick={() => bookSlot(s.id)} disabled={!canBookSlot}>
                      {canBookSlot ? 'Book' : 'Limit reached'}
                    </Button>
                  </div>
                ))}
            </div>
          </Card>
          <Card title="My Bookings">
            {bookings.length === 0 ? (
              <p className="text-slate-500 dark:text-slate-400 text-sm text-center py-6">No bookings yet.</p>
            ) : bookings.map(b => (
              <div key={b.id} className="p-3 portal-surface rounded-xl mb-2">
                <p className="font-medium text-sm">{b.slot_date} at {b.start_time}</p>
                <Badge variant={b.status === 'confirmed' ? 'success' : 'default'}>{b.status}</Badge>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Video room: {b.room}</p>
                <VideoCallPanel
                  roomName={b.room}
                  displayName={user?.name || 'Patient'}
                  bookingId={b.id}
                />
              </div>
            ))}
          </Card>
        </div>
      )}

      {tab === 'summaries' && <ConsultationSummariesPanel />}

      {tab === 'guardian' && <HealthGuardianPanel />}
    </DashboardLayout>
  )
}
