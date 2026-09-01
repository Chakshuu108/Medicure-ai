import { useEffect, useState } from 'react'
import { Card } from './ui/Card'
import { api, type MeetSummaryRecord } from '../lib/api'

export function ConsultationSummariesPanel() {
  const [summaries, setSummaries] = useState<MeetSummaryRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getMeetSummaries()
      .then(setSummaries)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Card><p className="text-slate-500 dark:text-slate-400 text-sm">Loading summaries...</p></Card>

  if (!summaries.length) {
    return (
      <Card title="Consultation Summaries">
        <p className="text-slate-500 dark:text-slate-400 text-sm text-center py-8">
          No summaries yet. Complete an Online OPD video call to generate one automatically.
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">📋 Consultation Summaries ({summaries.length})</h3>
      {summaries.map(s => {
        const summary = s.summary_json || {}
        const sufferings = summary.sufferings as string[] | undefined
        const medicines = summary.medicines_recommended as { medicine?: string }[] | undefined
        return (
          <Card key={s.id} title={`${s.slot_date} · ${s.start_time}`} subtitle={s.patient_name}>
            {summary.conclusion ? <p className="text-sm mb-2"><strong>Conclusion:</strong> {String(summary.conclusion)}</p> : null}
            {summary.disease ? <p className="text-sm mb-2"><strong>Disease:</strong> {String(summary.disease)}</p> : null}
            {sufferings?.length ? <p className="text-sm mb-2"><strong>Sufferings:</strong> {sufferings.join(', ')}</p> : null}
            {medicines?.length ? (
              <p className="text-sm mb-2"><strong>Medicines:</strong> {medicines.map(m => m.medicine).filter(Boolean).join(', ')}</p>
            ) : null}
            {summary.medicine_changes ? <p className="text-sm"><strong>Changes:</strong> {String(summary.medicine_changes)}</p> : null}
          </Card>
        )
      })}
    </div>
  )
}
