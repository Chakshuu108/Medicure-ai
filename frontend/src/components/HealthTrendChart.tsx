import {
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { TrendPoint } from '../lib/api'
import { useTheme } from '../context/ThemeContext'

interface HealthTrendChartProps {
  points: TrendPoint[]
  height?: number
  showRollingAvg?: boolean
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

export function HealthTrendChart({ points, height = 280, showRollingAvg = true }: HealthTrendChartProps) {
  const { isDark } = useTheme()
  const gridColor = isDark ? '#334155' : '#E2E8F0'
  const tickColor = isDark ? '#94A3B8' : '#64748B'
  const chartData = points.map(p => ({
    ...p,
    label: formatDate(p.date),
    score: p.missed ? null : p.total_score,
    avg: p.missed ? null : p.rolling_avg,
  }))

  if (chartData.length === 0) {
    return <p className="text-slate-500 dark:text-slate-400 text-sm text-center py-8">No trend data yet. Complete daily check-ins to see your chart.</p>
  }

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={chartData} margin={{ top: 12, right: 12, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: tickColor }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[-6, 6]}
            tick={{ fontSize: 11, fill: tickColor }}
            axisLine={false}
            tickLine={false}
            width={28}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const row = payload[0].payload as TrendPoint & { label: string; score: number | null }
              if (row.missed) {
                return (
                  <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-2 shadow text-sm text-slate-900 dark:text-slate-100">
                    <p className="font-medium">{row.label}</p>
                    <p className="text-amber-600">Missed check-in</p>
                  </div>
                )
              }
              return (
                <div className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-2 shadow text-sm text-slate-900 dark:text-slate-100">
                  <p className="font-medium">{row.label}</p>
                  <p>Score: <strong>{row.total_score}</strong></p>
                  <p>Status: {row.status}</p>
                  {row.rolling_avg != null && <p>3-day avg: {row.rolling_avg}</p>}
                </div>
              )
            }}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#6366F1"
            strokeWidth={2.5}
            dot={(props) => {
              const { cx, cy, payload } = props
              if (!cx || !cy) return null
              if (payload.missed) {
                return (
                  <g key={payload.date}>
                    <text x={cx} y={cy + 28} textAnchor="middle" fill="#D97706" fontSize={10} fontWeight={600}>
                      Missed
                    </text>
                  </g>
                )
              }
              const color = payload.status === 'Improving' ? '#34D399' : payload.status === 'Worsening' ? '#F87171' : '#FBBF24'
              return <circle key={payload.date} cx={cx} cy={cy} r={5} fill={color} stroke="#fff" strokeWidth={2} />
            }}
            connectNulls={false}
            name="Daily score"
          />
          {showRollingAvg && (
            <Line
              type="monotone"
              dataKey="avg"
              stroke="#BE123C"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
              name="3-day avg"
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
      <div className="flex flex-wrap gap-4 mt-2 text-xs text-slate-500 dark:text-slate-400 justify-center">
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-indigo-500 inline-block" /> Daily score</span>
        {showRollingAvg && <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-rose-700 inline-block" /> 3-day average</span>}
        <span className="text-amber-600 dark:text-amber-400 font-medium">Missed = no line, label shown</span>
      </div>
    </div>
  )
}
