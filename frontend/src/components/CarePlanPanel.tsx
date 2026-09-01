import { SchedulePanel } from './SchedulePanel'
import type { Prescription } from '../lib/api'

export function CarePlanPanel({
  prescriptions,
  onPrescriptionsChange,
}: {
  prescriptions: Prescription[]
  onPrescriptionsChange?: () => void
}) {
  return <SchedulePanel prescriptions={prescriptions} onPrescriptionsChange={onPrescriptionsChange} />
}
