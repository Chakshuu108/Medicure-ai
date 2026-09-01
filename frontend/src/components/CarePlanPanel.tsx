import { SchedulePanel } from './SchedulePanel'
import type { Prescription } from '../lib/api'

export function CarePlanPanel({ prescriptions }: { prescriptions: Prescription[] }) {
  return <SchedulePanel prescriptions={prescriptions} />
}
