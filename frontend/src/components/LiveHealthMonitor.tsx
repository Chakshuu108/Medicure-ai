import { useEffect, useMemo, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Activity,
  AlertTriangle,
  Bell,
  Calendar,
  CheckCircle2,
  Pill,
  Shield,
  Stethoscope,
  TrendingUp,
} from 'lucide-react'

export interface LiveMonitorData {
  completedDays: number
  missedDays: number
  daysSilent: number
  latestStatus: string
  trend: string
  checkinCount: number
  unresolvedAlerts: number
  guardianAlertsSent: number
  lastScanAt?: string
  nextAppointment?: string
  medsToday?: number
  autonomousActions: string[]
}

const SCAN_AGENTS = [
  'Check-in history',
  'Medication schedule',
  'Symptom patterns',
  'Missed-day alerts',
  'Doctor escalation',
]

function trendColor(trend: string) {
  const t = trend.toLowerCase()
  if (t.includes('improv') || t.includes('stable') || t === 'good') return '#34d399'
  if (t.includes('wors') || t.includes('declin')) return '#f87171'
  return '#fbbf24'
}

function adherencePct(completed: number, missed: number) {
  const total = completed + missed
  if (!total) return 0
  return Math.round((completed / total) * 100)
}

export function LiveHealthMonitor({ data }: { data: LiveMonitorData }) {
  const [taskIdx, setTaskIdx] = useState(0)
  const [agentIdx, setAgentIdx] = useState(0)
  const pct = adherencePct(data.completedDays, data.missedDays)

  const liveTasks = useMemo(() => {
    const tasks = [
      { icon: CheckCircle2, label: 'Daily check-ins', value: `${data.completedDays} done · ${data.missedDays} missed`, color: '#34d399' },
      { icon: Activity, label: 'Days since last log', value: data.daysSilent === 0 ? 'Logged today' : `${data.daysSilent} day(s) silent`, color: data.daysSilent > 2 ? '#f87171' : '#60a5fa' },
      { icon: TrendingUp, label: 'Current status', value: data.latestStatus || 'Monitoring', color: trendColor(data.trend) },
      { icon: TrendingUp, label: 'Health trend', value: data.trend || 'Collecting data…', color: trendColor(data.trend) },
      { icon: Bell, label: 'Doctor notified', value: data.guardianAlertsSent > 0 ? `${data.guardianAlertsSent} alert(s) sent` : 'No new alerts', color: data.guardianAlertsSent > 0 ? '#f87171' : '#34d399' },
      { icon: Shield, label: 'Sessions analysed', value: `${data.checkinCount} check-in(s)`, color: '#a78bfa' },
      { icon: AlertTriangle, label: 'Open alerts', value: data.unresolvedAlerts > 0 ? `${data.unresolvedAlerts} need attention` : 'None open', color: data.unresolvedAlerts > 0 ? '#fbbf24' : '#34d399' },
    ]
    if (data.nextAppointment) {
      tasks.push({ icon: Calendar, label: 'Next appointment', value: data.nextAppointment, color: '#60a5fa' })
    }
    if (data.medsToday != null && data.medsToday > 0) {
      tasks.push({ icon: Pill, label: 'Medicines today', value: `${data.medsToday} dose(s) scheduled`, color: '#f472b6' })
    }
    return tasks
  }, [data])

  const feed = data.autonomousActions.length
    ? data.autonomousActions
    : ['Background monitoring active', 'Waiting for health data…']

  useEffect(() => {
    const t = setInterval(() => setTaskIdx(i => (i + 1) % liveTasks.length), 2800)
    return () => clearInterval(t)
  }, [liveTasks.length])

  useEffect(() => {
    const t = setInterval(() => setAgentIdx(i => (i + 1) % SCAN_AGENTS.length), 2400)
    return () => clearInterval(t)
  }, [])

  const active = liveTasks[taskIdx]

  return (
    <div className="relative w-full max-w-md ml-auto h-full min-h-[360px] rounded-2xl bg-gradient-to-bl from-slate-900 via-slate-900 to-violet-950 border border-violet-400/30 shadow-2xl shadow-violet-900/40 overflow-hidden flex flex-col">
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle at 90% 20%, rgba(139,92,246,0.55), transparent 45%), radial-gradient(circle at 70% 80%, rgba(59,130,246,0.2), transparent 40%)',
        }}
      />

      {/* Scan sweep */}
      <motion.div
        className="absolute inset-0 pointer-events-none bg-gradient-to-b from-violet-500/10 via-transparent to-transparent"
        animate={{ y: ['-100%', '200%'] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
      />

      <div className="relative z-10 p-4 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center gap-2">
          <motion.span
            className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
            animate={{ opacity: [1, 0.35, 1], scale: [1, 1.15, 1] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          />
          <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Live guardian</span>
        </div>
        {data.lastScanAt && (
          <span className="text-[10px] text-slate-400">
            Last scan {new Date(data.lastScanAt).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      <div className="relative z-10 px-4 pt-2">
        <motion.p
          key={agentIdx}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-[11px] text-violet-300 font-medium text-right"
        >
          Analysing: <span className="text-white">{SCAN_AGENTS[agentIdx]}</span>
        </motion.p>
      </div>

      {/* Adherence ring — right aligned */}
      <div className="relative z-10 flex justify-end px-6 py-3">
        <div className="relative w-40 h-40">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="7" />
            <motion.circle
              cx="50" cy="50" r="42" fill="none"
              stroke={pct >= 70 ? '#34d399' : pct >= 40 ? '#fbbf24' : '#f87171'}
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={`${pct * 2.64} 264`}
              initial={{ strokeDasharray: '0 264' }}
              animate={{ strokeDasharray: `${pct * 2.64} 264` }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.span
              key={pct}
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="text-3xl font-bold text-white tabular-nums"
            >
              {pct}%
            </motion.span>
            <span className="text-[10px] text-slate-400 uppercase tracking-wide text-center leading-tight">
              Check-in<br />adherence
            </span>
          </div>
          {[0, 1, 2, 3].map(i => (
            <motion.span
              key={i}
              className="absolute w-1.5 h-1.5 rounded-full bg-violet-400/80"
              style={{ top: '50%', left: '50%', marginTop: -3, marginLeft: -3 }}
              animate={{
                x: [0, Math.cos((i * Math.PI) / 2) * 72, 0],
                y: [0, Math.sin((i * Math.PI) / 2) * 72, 0],
                opacity: [0.2, 0.9, 0.2],
              }}
              transition={{ duration: 3, repeat: Infinity, delay: i * 0.5 }}
            />
          ))}
        </div>
      </div>

      {/* Data flow pipeline */}
      <div className="relative z-10 px-4 pb-2">
        <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1 px-1">
          <span>Your data</span>
          <span>Guardian AI</span>
          <span>Doctor</span>
        </div>
        <div className="flex items-center gap-1">
          {['You', 'AI', 'Dr'].map((node, i) => (
            <div key={node} className="flex items-center flex-1">
              <motion.div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0
                  ${i === 0 ? 'bg-blue-500/20 text-blue-300 border border-blue-500/35' : ''}
                  ${i === 1 ? 'bg-violet-500/35 text-violet-100 border border-violet-400/50 shadow-lg shadow-violet-500/20' : ''}
                  ${i === 2 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/35' : ''}`}
                animate={{ scale: [1, 1.06, 1], boxShadow: i === 1 ? ['0 0 0 rgba(139,92,246,0)', '0 0 16px rgba(139,92,246,0.45)', '0 0 0 rgba(139,92,246,0)'] : undefined }}
                transition={{ duration: 2.2, repeat: Infinity, delay: i * 0.35 }}
              >
                {i === 1 ? <Shield className="w-4 h-4" /> : i === 2 ? <Stethoscope className="w-4 h-4" /> : <Activity className="w-4 h-4" />}
              </motion.div>
              {i < 2 && (
                <div className="flex-1 h-0.5 bg-slate-700/80 relative mx-1 overflow-hidden rounded-full">
                  <motion.div
                    className="absolute inset-y-0 w-4 bg-gradient-to-r from-transparent via-violet-300 to-transparent"
                    animate={{ left: ['-16px', '110%'] }}
                    transition={{ duration: 1.6, repeat: Infinity, delay: i * 0.55, ease: 'linear' }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
        <p className="text-[10px] text-slate-500 text-right mt-1.5">
          {data.guardianAlertsSent > 0
            ? `${data.guardianAlertsSent} finding(s) routed to your doctor`
            : 'Monitoring — no escalation needed'}
        </p>
      </div>

      {/* Active metric card */}
      <div className="relative z-10 px-4 py-2 flex-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={taskIdx}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            transition={{ duration: 0.35 }}
            className="rounded-xl bg-white/[0.07] border border-white/10 p-3 backdrop-blur-md"
          >
            <div className="flex items-start gap-3">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                style={{ backgroundColor: `${active.color}22`, border: `1px solid ${active.color}55` }}
              >
                <active.icon className="w-4 h-4" style={{ color: active.color }} />
              </div>
              <div className="min-w-0 flex-1 text-right">
                <p className="text-[10px] uppercase tracking-wider text-slate-500">{active.label}</p>
                <p className="text-sm font-semibold text-white mt-0.5">{active.value}</p>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>

        <div className="mt-3 space-y-2">
          {[
            { label: 'Completed check-ins', val: data.completedDays, max: Math.max(data.completedDays + data.missedDays, 1), color: '#34d399' },
            { label: 'Missed check-ins', val: data.missedDays, max: Math.max(data.completedDays + data.missedDays, 1), color: '#f87171' },
          ].map(bar => (
            <div key={bar.label}>
              <div className="flex justify-between text-[10px] text-slate-500 mb-0.5">
                <span>{bar.val}</span>
                <span>{bar.label}</span>
              </div>
              <div className="h-2 bg-slate-800/80 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full ml-auto"
                  style={{ backgroundColor: bar.color, originX: 1 }}
                  initial={{ width: 0 }}
                  animate={{ width: `${(bar.val / bar.max) * 100}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut' }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Scrolling autonomous log */}
      <div className="relative z-10 border-t border-white/5 bg-black/35 py-2 overflow-hidden mt-auto">
        <motion.div
          className="flex gap-8 whitespace-nowrap text-[10px] text-slate-400"
          animate={{ x: ['0%', '-50%'] }}
          transition={{ duration: 16, repeat: Infinity, ease: 'linear' }}
        >
          {[...feed, ...feed].map((line, i) => (
            <span key={i} className="inline-flex items-center gap-1.5 shrink-0">
              <span className="w-1 h-1 rounded-full bg-violet-400" />
              {line}
            </span>
          ))}
        </motion.div>
      </div>
    </div>
  )
}
