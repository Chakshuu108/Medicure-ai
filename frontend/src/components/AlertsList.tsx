import { Badge, Card } from './ui/Card'
import { Button } from './ui/Button'
import type { Alert } from '../lib/api'

const LEVEL_STYLES: Record<string, 'danger' | 'warning' | 'success' | 'default'> = {
  severe: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'success',
}

function levelBadge(severity: string, label?: string) {
  const key = severity.toLowerCase()
  return (
    <Badge variant={LEVEL_STYLES[key] || 'default'}>
      {label || key.charAt(0).toUpperCase() + key.slice(1)}
    </Badge>
  )
}

export function AlertsList({
  alerts,
  role,
  onResolve,
}: {
  alerts: Alert[]
  role: 'patient' | 'doctor'
  onResolve?: (id: string) => void
}) {
  if (alerts.length === 0) {
    return (
      <Card>
        <p className="text-center text-slate-500 dark:text-slate-400 py-8">
          {role === 'doctor' ? 'No patient alerts right now.' : 'No health alerts for you right now.'}
        </p>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      {alerts.map(a => (
        <Card key={a.id} className={`!p-4 border-l-4 ${
          a.severity === 'severe' || a.severity === 'high'
            ? 'border-l-red-400'
            : a.severity === 'medium'
              ? 'border-l-amber-400'
              : 'border-l-emerald-400'
        }`}>
          <div className="flex justify-between items-start gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                {levelBadge(a.severity, a.severity_label)}
                {role === 'doctor' && a.patient_name && (
                  <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">{a.patient_name}</span>
                )}
                {a.resolved && (
                  <span className="text-xs text-slate-400">Resolved</span>
                )}
              </div>
              <p className="text-base font-medium text-slate-900 dark:text-slate-100 leading-snug">
                {a.summary || a.alert_type_label || 'Health alert'}
              </p>
              {role === 'patient' && !a.resolved && (
                <p className="text-sm text-primary-700 dark:text-primary-300 mt-2">Your doctor has been notified.</p>
              )}
              <p className="text-xs text-slate-400 mt-2">
                {new Date(a.created_at).toLocaleString('en-IN', {
                  day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
                })}
              </p>
            </div>
            {role === 'doctor' && !a.resolved && onResolve && (
              <Button size="sm" variant="secondary" onClick={() => onResolve(a.id)}>
                Mark done
              </Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}
