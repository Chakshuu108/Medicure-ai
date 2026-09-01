import { useEffect, useState } from 'react'
import { Calendar, RefreshCw } from 'lucide-react'
import { Card } from './ui/Card'
import { Button } from './ui/Button'
import { api, type Prescription, type ScheduleItem } from '../lib/api'
import { useAuth } from '../context/AuthContext'

function formatAddedDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function SchedulePanel({ prescriptions = [] }: { prescriptions?: Prescription[] }) {
  const { user } = useAuth()
  const [schedule, setSchedule] = useState<ScheduleItem[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const googleEmail = (user?.extra?.google_email as string) || user?.extra?.calendar_connected ? 'your Google account' : ''
  const sortedPrescriptions = [...prescriptions].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  useEffect(() => {
    api.getSchedulePreview()
      .then(data => setSchedule(data.schedule))
      .catch(() => setSchedule([]))
      .finally(() => setLoading(false))
  }, [])

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
            Missed health check-in reminders are also added to your calendar automatically.
          </p>
          {message && <p className="text-sm text-emerald-700 dark:text-emerald-300">{message}</p>}
          {error && <p className="text-sm text-red-600 dark:text-red-300">{error}</p>}

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">My Prescriptions</h4>
            {sortedPrescriptions.length === 0 ? (
              <p className="text-xs text-slate-500 dark:text-slate-400 text-center py-4">No prescriptions yet.</p>
            ) : (
              <div className="space-y-3">
                {sortedPrescriptions.map(rx => (
                  <div
                    key={rx.id}
                    className="rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden"
                  >
                    <div className="px-3 py-2 bg-primary-50/80 dark:bg-primary-950/40 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between gap-2">
                      <span className="text-xs font-semibold text-slate-600 dark:text-slate-300">Added on</span>
                      <span className="text-xs font-semibold text-primary-600 dark:text-primary-400">
                        {formatAddedDate(rx.created_at)}
                      </span>
                    </div>
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="bg-slate-50 dark:bg-slate-800/60 text-left">
                          <th className="px-2.5 py-2 font-semibold text-slate-600 dark:text-slate-300">Medicine</th>
                          <th className="px-2.5 py-2 font-semibold text-slate-600 dark:text-slate-300">Dose</th>
                          <th className="px-2.5 py-2 font-semibold text-slate-600 dark:text-slate-300">Timing</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rx.medicines.map((m, i) => (
                          <tr
                            key={`${rx.id}-${i}`}
                            className="border-t border-slate-100 dark:border-slate-800"
                          >
                            <td className="px-2.5 py-2 font-medium text-slate-900 dark:text-slate-100">{m.name}</td>
                            <td className="px-2.5 py-2 text-slate-600 dark:text-slate-400">{m.dosage}</td>
                            <td className="px-2.5 py-2 text-slate-500 dark:text-slate-400 capitalize">{m.timing}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
            No schedule available. Ask your doctor to create a prescription.
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
                  <th className="px-3 py-2.5 font-semibold text-slate-600 dark:text-slate-300 hidden sm:table-cell">Timing</th>
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
                      <td className="px-3 py-2.5 text-slate-500 dark:text-slate-400 capitalize hidden sm:table-cell">{item.timing}</td>
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
