export const FREQUENCY_OPTIONS = [
  { value: 'once', label: 'Once only (single dose)' },
  { value: 'daily', label: 'Every day' },
  { value: 'alternate_days', label: 'Alternate days (every 2 days)' },
  { value: 'every_3_days', label: 'Every 3 days' },
  { value: 'weekly', label: 'Once a week' },
  { value: 'as_needed', label: 'As needed (PRN — no fixed schedule)' },
] as const

export type FrequencyPattern = (typeof FREQUENCY_OPTIONS)[number]['value']

export function frequencyLabel(pattern: string): string {
  return FREQUENCY_OPTIONS.find(o => o.value === pattern)?.label ?? pattern.replace(/_/g, ' ')
}

export function defaultMedicineRow() {
  return {
    name: '',
    disease: '',
    dosage: '',
    duration_days: 7,
    frequency_pattern: 'daily' as FrequencyPattern,
    times_per_day: 1,
  }
}

const DOSE_OFFSET_HOURS: Record<number, number[]> = {
  1: [0],
  2: [0, 12],
  3: [0, 6, 12],
  4: [0, 6, 12, 18],
  5: [0, 5, 10, 15, 20],
  6: [0, 4, 8, 12, 16, 20],
}

export function computeDoseTimes(startTime: string, timesPerDay: number): string[] {
  const [h, m] = startTime.split(':').map(Number)
  if (!Number.isFinite(h) || timesPerDay < 1) return [startTime || '08:00']
  const offsets = DOSE_OFFSET_HOURS[timesPerDay] || Array.from({ length: timesPerDay }, (_, i) => i * (20 / Math.max(timesPerDay - 1, 1)))
  return offsets.map(offset => {
    const totalMinutes = h * 60 + (m || 0) + Math.round(offset * 60)
    const capped = Math.min(totalMinutes, 22 * 60)
    const hh = Math.floor(capped / 60)
    const mm = capped % 60
    return `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`
  })
}

export function scheduleSummary(m: {
  frequency_pattern?: string
  times_per_day?: number
  duration_days?: number
}): string {
  const freq = frequencyLabel(m.frequency_pattern || 'daily')
  if (m.frequency_pattern === 'as_needed') return freq
  if (m.frequency_pattern === 'once') return 'Single dose'
  const times = m.times_per_day ?? 1
  const days = m.duration_days ?? 7
  return `${times}× per day · ${days} day${days === 1 ? '' : 's'} · ${freq}`
}
