import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Bot, RefreshCw, Shield, Sparkles, Zap } from 'lucide-react'
import { Card, Badge } from './ui/Card'
import { Button } from './ui/Button'
import { HealthTrendChart } from './HealthTrendChart'
import { LiveHealthMonitor } from './LiveHealthMonitor'
import { api, type CareAutopilotData } from '../lib/api'

const SEV_COLORS: Record<string, 'danger' | 'warning' | 'success' | 'default'> = {
  high: 'danger',
  severe: 'danger',
  medium: 'warning',
  low: 'success',
}

export function HealthGuardianPanel() {
  const [data, setData] = useState<CareAutopilotData | null>(null)
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)

  const load = () => {
    setLoading(true)
    api.getCareAutopilot()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const runScan = async () => {
    setScanning(true)
    try {
      await api.runGuardianCheck(true)
      load()
    } finally {
      setScanning(false)
    }
  }

  if (loading && !data) {
    return (
      <Card>
        <div className="flex items-center justify-center gap-2 py-16 text-slate-500 dark:text-slate-400">
          <RefreshCw className="w-5 h-5 animate-spin" />
          Health Guardian is starting…
        </div>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <p className="text-center text-slate-500 dark:text-slate-400 py-8">Could not load Health Guardian.</p>
        <Button onClick={load} className="mx-auto block">Retry</Button>
      </Card>
    )
  }

  const guardian = data.guardian || {}
  const reasoning = guardian.reasoning || {}
  const actions = guardian.actions || {}
  const findings = reasoning.findings || []
  const alertsSent = actions.alerts_sent || 0
  const ranAt = guardian.ran_at ? new Date(guardian.ran_at).toLocaleString('en-IN') : ''
  const trends = data.trends || guardian.trends
  const snapshot = guardian.snapshot || {}
  const proactiveRanAt = data.proactive_monitor?.ran_at

  const monitorData = {
    completedDays: trends?.summary?.completed_days ?? 0,
    missedDays: trends?.summary?.missed_days ?? 0,
    daysSilent: snapshot.days_silent ?? 0,
    latestStatus: trends?.summary?.latest_status ?? '—',
    trend: trends?.summary?.trend ?? '—',
    checkinCount: snapshot.checkin_count ?? 0,
    unresolvedAlerts: snapshot.unresolved_alerts ?? data.alerts.filter(a => !a.resolved).length,
    guardianAlertsSent: alertsSent,
    lastScanAt: proactiveRanAt || guardian.ran_at,
    autonomousActions: data.autonomous_actions,
  }

  return (
    <div className="space-y-6">
      <Card className="!p-4 bg-primary-50/40 dark:bg-primary-950/30 border border-primary-100 dark:border-primary-900">
        <div className="flex flex-wrap items-start gap-3">
          <Shield className="w-5 h-5 text-primary-600 dark:text-primary-400 mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-slate-900 dark:text-slate-100">Proactive monitoring is active</p>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Health Guardian runs in the background even when you are offline — missed check-in reminders,
              silence alerts to your doctor, and periodic wellness scans.
            </p>
            {proactiveRanAt ? (
              <p className="text-xs text-slate-500 mt-2">
                Last system scan: <strong>{new Date(proactiveRanAt).toLocaleString('en-IN')}</strong>
              </p>
            ) : (
              <p className="text-xs text-slate-500 mt-2">First background scan runs shortly after server start.</p>
            )}
          </div>
          <Badge variant="success">24/7</Badge>
        </div>
      </Card>

      {/* Hero: content left, live monitor right */}
      <Card className="!p-0 overflow-hidden bg-gradient-to-br from-violet-600 via-primary-700 to-indigo-800 text-white">
        <div className="grid lg:grid-cols-[1.15fr_0.85fr] gap-0">
          <div className="p-6 lg:p-8 flex flex-col justify-center order-2 lg:order-1">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5" />
              <span className="text-xs font-bold uppercase tracking-wider text-white/75">
                Health Guardian · Autonomous
              </span>
            </div>
            <h2 className="text-2xl lg:text-3xl font-bold leading-tight">
              {reasoning.overall_assessment || data.patient_message || 'Your health is being watched 24/7'}
            </h2>
            {(reasoning.patient_message || data.patient_message) && (
              <p className="text-white/85 mt-3 text-sm leading-relaxed max-w-lg">
                {reasoning.patient_message || data.patient_message}
              </p>
            )}
            <div className="flex flex-wrap gap-2 mt-4">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-white/15 text-white border border-white/25">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-300 animate-pulse inline-block mr-1.5" />
                Live · {guardian.cached ? 'Cached today' : 'Fresh scan'}
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border border-white/25 bg-white/15 text-white ${alertsSent > 0 ? 'text-red-100' : ''}`}>
                {alertsSent > 0 ? `${alertsSent} doctor alert(s)` : 'All clear'}
              </span>
            </div>
            {ranAt && <p className="text-xs text-white/50 mt-3">Last analysis: {ranAt}</p>}
            {actions.appointment_imminent && (
              <p className="text-sm text-amber-200 font-medium mt-2">
                Appointment within 48h — priority escalated.
              </p>
            )}
          </div>
          <div className="p-4 lg:p-6 lg:pr-8 flex items-center justify-end order-1 lg:order-2 bg-black/15 lg:bg-transparent">
            <LiveHealthMonitor data={monitorData} />
          </div>
        </div>
      </Card>

      {/* Quick stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Check-ins done', value: monitorData.completedDays },
          { label: 'Missed days', value: monitorData.missedDays, warn: monitorData.missedDays > 0 },
          { label: 'Status', value: monitorData.latestStatus, cap: true },
          { label: 'Trend', value: monitorData.trend, cap: true },
        ].map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 p-3 shadow-sm"
          >
            <p className="text-xs text-slate-500">{s.label}</p>
            <p className={`text-lg font-bold mt-0.5 capitalize ${s.warn ? 'text-amber-600 dark:text-amber-400' : 'text-slate-900 dark:text-slate-100'}`}>
              {s.value}
            </p>
          </motion.div>
        ))}
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <Card title="Today's priorities" subtitle="What to focus on right now">
          <ul className="space-y-2">
            {data.priorities.map((p, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-700 dark:text-slate-300">
                <Zap className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                {p}
              </li>
            ))}
          </ul>
        </Card>
        <Card title="Autonomous actions" subtitle="Ran in the background without you logging in">
          <ul className="space-y-2">
            {data.autonomous_actions.map((a, i) => (
              <li key={i} className="flex gap-2 text-sm text-slate-600 dark:text-slate-400">
                <Bot className="w-4 h-4 text-primary-500 shrink-0 mt-0.5" />
                {a}
              </li>
            ))}
          </ul>
          {proactiveRanAt && (
            <p className="text-xs text-slate-400 mt-3">
              Last system scan: {new Date(proactiveRanAt).toLocaleString('en-IN')}
            </p>
          )}
        </Card>
      </div>

      {trends?.points?.length ? (
        <Card title="Health trend" subtitle="Daily scores — missed days shown separately">
          <HealthTrendChart points={trends.points} />
        </Card>
      ) : null}

      {findings.length === 0 ? (
        <Card>
          <div className="text-center py-6">
            <div className="text-3xl mb-2">🟢</div>
            <p className="font-medium text-slate-800 dark:text-slate-200">No concerns flagged right now</p>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Keep up your daily check-ins.</p>
          </div>
        </Card>
      ) : (
        <div className="space-y-3">
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">What Guardian noticed ({findings.length})</h3>
          {findings.map((f, i) => (
            <Card key={i} className="!p-4 border-l-4 border-l-primary-400">
              <div className="flex flex-wrap items-start justify-between gap-2 mb-1">
                <p className="font-semibold text-slate-900 dark:text-slate-100">{f.title}</p>
                <Badge variant={SEV_COLORS[f.severity] || 'default'}>
                  {(f.severity || 'low').charAt(0).toUpperCase() + (f.severity || 'low').slice(1)}
                </Badge>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400">{f.description}</p>
            </Card>
          ))}
        </div>
      )}

      {actions.action_log && actions.action_log.length > 0 && (
        <Card title="Guardian action log" subtitle="Steps taken this session">
          <div className="space-y-2">
            {actions.action_log.map((entry, i) => (
              <div key={i} className="flex gap-3 text-sm py-2 border-b border-slate-50 dark:border-slate-800 last:border-0">
                <span>{entry.action === 'alert_sent' ? '🔔' : entry.action === 'monitor' ? '👁️' : '📋'}</span>
                <div>
                  <p className="font-medium text-slate-800 dark:text-slate-200">{entry.finding}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{entry.severity} · {entry.timestamp?.slice(11, 19)}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <div className="flex flex-wrap gap-3">
        <Button onClick={runScan} loading={scanning}>
          <Shield className="w-4 h-4" /> Run full health scan
        </Button>
        <Button variant="secondary" onClick={load} loading={loading}>
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>
    </div>
  )
}
