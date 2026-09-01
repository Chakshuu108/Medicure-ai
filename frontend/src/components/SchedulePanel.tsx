import { useCallback, useEffect, useState } from 'react'
import { Calendar, RefreshCw } from 'lucide-react'
import { Card } from './ui/Card'
import { Button } from './ui/Button'
import { api, type Prescription, type PrescriptionMedicine, type ScheduleItem } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { computeDoseTimes, frequencyLabel, scheduleSummary } from '../lib/medicineSchedule'

function formatAddedDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function SchedulePanel({ prescriptions = [], onPrescriptionsChange }: {
  prescriptions?: Prescription[]
  onPrescriptionsChange?: () => void
}) {
  const { user } = useAuth()
  const [schedule, setSchedule] = useState<ScheduleItem[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [startForms, setStartForms] = useState<Record<string, { start_date: string; start_time: string }>>({})
  const [savingId, setSavingId] = useState<string | null>(null)

  const googleEmail = (user?.extra?.google_email as string) || user?.extra?.calendar_connected ? 'your Google account' : ''
  const sortedPrescriptions = [...prescriptions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  const loadSchedule = useCallback(() => {
    setLoading(true)
    api.getSchedulePreview()
      .then(data => setSchedule(data.schedule))
      .catch(() => setSchedule([]))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadSchedule()
  }, [loadSchedule, prescriptions])

  useEffect(() => {
    const next: Record<string, { start_date: string; start_time: string }> = {}
    for (const rx of sortedPrescriptions) {
      for (const m of rx.medicines) {
        next[m.id] = {
          start_date: m.start_date || new Date().toISOString().slice(0, 10),
          start_time: m.start_time || '08:00',
        }
      }
    }
    setStartForms(next)
  }, [prescriptions])

  const syncCalendar = async () => {
    setSyncing(true)
    setMessage('')
    setError('')
    try {
      const result = await api.syncToGoogleCalendar()
      if (result.success) setMessage(result.message)
      else setError(result.message)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sync failed. Sign out and sign in again with Google.')
    } finally {
      setSyncing(false)
    }
  }

  const saveMedicineStart = async (medicine: PrescriptionMedicine) => {
    const form = startForms[medicine.id]
    if (!form?.start_date || !form?.start_time) {
      setError('Choose a start date and time.')
      return
    }
    setSavingId(medicine.id)
    setError('')
    try {
      const dose_times = computeDoseTimes(form.start_time, medicine.times_per_day || 1)
      await api.updateMedicineSchedule(medicine.id, {
        start_date: form.start_date,
        start_time: form.start_time,
        dose_times,
      })
      setMessage(`Schedule updated for ${medicine.name}.`)
      onPrescriptionsChange?.()
      loadSchedule()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save schedule')
    } finally {
      setSavingId(null)
    }
  }

  let currentDate = ''

  return (
    <div className="grid lg:grid-cols-5 gap-6">
      <Card
        title="Google Calendar"
        subtitle="Sync doses · view prescriptions"
        className="lg:col-span-2"
      >
        <div className="space-y-4">
          <div className="p-3 portal-banner-success">
            Calendar linked via Google login
            {googleEmail && <span className="block text-xs mt-1 opacity-90">{googleEmail}</span>}
          </div>
          <Button onClick={syncCalendar} loading={syncing} className="w-full">
            <Calendar className="w-4 h-4 mr-2" />
            Sync Medicines to Calendar
          </Button>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Set a start date & time for each medicine below, then sync reminders to Google Calendar.
          </p>
          {message && <p className="text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
          {error && <p className="text-sm text-red-600 dark:text-red-300">{error}</p>}

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">My Prescriptions</h4>
            {sortedPrescriptions.length === 0 ? (
              <p className="text-xs text-slate-500 dark:text-slate-400 text-center py-4">No prescriptions yet.</p>
            ) : (
              <div className="space-y-4">
                {sortedPrescriptions.map(rx => (
                  <div key={rx.id} className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                    <div className="px-3 py-2 bg-primary-50/80 dark:bg-primary-950/40 border-b border-slate-100 dark:border-slate-700">
                      <p className="text-xs font-semibold text-primary-700 dark:text-primary-300">
                        {rx.disease || 'Prescription'} · {formatAddedDate(rx.created_at)}
                      </p>
                    </div>
                    <div className="p-3 space-y-4">
                      {rx.medicines.map(m => (
                        <div key={m.id} className="text-xs border-b border-slate-100 dark:border-slate-800 last:border-0 pb-3 last:pb-0">
                          <p className="font-semibold text-slate-900 dark:text-slate-100">{m.name}</p>
                          <p className="text-slate-500 mt-0.5">
                            {m.dosage} · {scheduleSummary(m)}
                          </p>
                          <p className="text-slate-500 capitalize">{frequencyLabel(m.frequency_pattern)}</p>
                          {m.frequency_pattern !== 'as_needed' && (
                            <div className="mt-2 space-y-2">
                              <div className="grid grid-cols-2 gap-2">
                                <input
                                  type="date"
                                  value={startForms[m.id]?.start_date || ''}
                                  onChange={e => setStartForms(f => ({
                                    ...f,
                                    [m.id]: { ...f[m.id], start_date: e.target.value },
                                  }))}
                                  className="portal-input text-xs py-1.5"
                                />
                                <input
                                  type="time"
                                  value={startForms[m.id]?.start_time || ''}
                                  onChange={e => setStartForms(f => ({
                                    ...f,
                                    [m.id]: { ...f[m.id], start_time: e.target.value },
                                  }))}
                                  className="portal-input text-xs py-1.5"
                                />
                              </div>
                              {m.times_per_day > 1 && startForms[m.id]?.start_time && (
                                <p className="text-slate-500">
                                  Dose times: {computeDoseTimes(startForms[m.id].start_time, m.times_per_day).join(', ')}
                                </p>
                              )}
                              <Button
                                size="sm"
                                loading={savingId === m.id}
                                onClick={() => saveMedicineStart(m)}
                                className="w-full"
                              >
                                {m.schedule_ready ? 'Update start schedule' : 'Start medicine from this date'}
                              </Button>
                            </div>
                          )}
                          {m.frequency_pattern === 'as_needed' && (
                            <p className="text-amber-700 dark:text-amber-300 mt-1">Take only when needed — no fixed schedule.</p>
                          )}
                        </div>
                      ))}
                    </div>
                    {rx.doctor_notes && (
                      <p className="px-3 py-2 text-xs text-slate-500 dark:text-slate-400 italic border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30">
                        {rx.doctor_notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </Card>

      <Card title="Medication Schedule" subtitle="Upcoming doses from your prescriptions" className="lg:col-span-3">
        {loading ? (
          <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 py-8 justify-center">
            <RefreshCw className="w-4 h-4 animate-spin" />
            Loading schedule...
          </div>
        ) : schedule.length === 0 ? (
          <p className="text-slate-500 dark:text-slate-400 text-center py-8">
            Set a start date & time for each medicine to generate your dose schedule.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-100 dark:border-slate-800">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/80 text-left">
                  <th className="px-3 py-2.5 font-semibold text-slate-600 dark:text-slate-300 w-28">Date</th>
                  <th className="px-3 py-2.5 font-semibold text-slate-600 dark:text-slate-300 w-20">Time</th>
                  <th className="px-3 py-2.5 font-semibold text-slate-600 dark:text-slate-300">Medicine</th>
                  <th className="px-3 py-2.5 font-semibold text-slate-600 dark:text-slate-300">Dosage</th>
                  <th className="px-3 py-2.5 font-semibold text-slate-600 dark:text-slate-300 hidden sm:table-cell">Pattern</th>
                </tr>
              </thead>
              <tbody>
                {schedule.map((item, i) => {
                  const showDate = item.date !== currentDate
                  if (showDate) currentDate = item.date
                  return (
                    <tr
                      key={`${item.date}-${item.time}-${item.medicine}-${i}`}
                      className={`border-t border-slate-100 dark:border-slate-800 hover:bg-slate-50/80 dark:hover:bg-slate-800/40
                        ${showDate ? 'bg-primary-50/30 dark:bg-primary-950/20' : ''}`}
                    >
                      <td className="px-3 py-2.5 font-medium text-slate-800 dark:text-slate-200 whitespace-nowrap">
                        {showDate ? item.date : ''}
                      </td>
                      <td className="px-3 py-2.5 font-mono text-primary-600 dark:text-primary-400">{item.time}</td>
                      <td className="px-3 py-2.5 font-medium text-slate-900 dark:text-slate-100">{item.medicine}</td>
                      <td className="px-3 py-2.5 text-slate-600 dark:text-slate-400">{item.dosage}</td>
                      <td className="px-3 py-2.5 text-slate-500 dark:text-slate-400 hidden sm:table-cell">{item.timing}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
