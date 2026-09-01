import { useState, useEffect } from 'react'
import { DashboardLayout, DoctorTabs } from '../components/Layout'
import { VideoCallPanel } from '../components/VideoCallPanel'
import { AlertsList } from '../components/AlertsList'
import { ConsultationSummariesPanel } from '../components/ConsultationSummariesPanel'
import { Card, Badge } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { api, type Patient, type Alert, type DoctorSlot } from '../lib/api'
import { useAuth } from '../context/AuthContext'
import { FREQUENCY_OPTIONS, defaultMedicineRow, type FrequencyPattern } from '../lib/medicineSchedule'

type MedicineFormRow = ReturnType<typeof defaultMedicineRow>

function emptyRxForm(disease = '') {
  return { disease, notes: '', medicines: [defaultMedicineRow()] as MedicineFormRow[] }
}

export function DoctorDashboard() {
  const [tab, setTab] = useState('patients')
  const { user } = useAuth()
  const [patients, setPatients] = useState<Patient[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [slots, setSlots] = useState<DoctorSlot[]>([])
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)
  const [rxForm, setRxForm] = useState(emptyRxForm())
  const [slotForm, setSlotForm] = useState({ slot_date: '' })
  const [rxMsg, setRxMsg] = useState('')
  const [rxError, setRxError] = useState('')

  useEffect(() => {
    api.getPatients().then(setPatients).catch(() => {})
    if (tab === 'alerts') api.getAlerts().then(setAlerts).catch(() => {})
    if (tab === 'opd') api.getDoctorSlots().then(setSlots).catch(() => {})
  }, [tab])

  useEffect(() => {
    if (selectedPatient) setRxForm(emptyRxForm(selectedPatient.disease || ''))
  }, [selectedPatient?.id])

  const updateMedicine = (index: number, patch: Partial<MedicineFormRow>) => {
    setRxForm(f => {
      const medicines = [...f.medicines]
      medicines[index] = { ...medicines[index], ...patch }
      return { ...f, medicines }
    })
  }

  const createPrescription = async () => {
    if (!selectedPatient) return
    setRxError('')
    setRxMsg('')
    const meds = rxForm.medicines.filter(m => m.name.trim())
    if (!rxForm.disease.trim()) {
      setRxError('Enter the disease / diagnosis for this prescription.')
      return
    }
    if (!meds.length) {
      setRxError('Add at least one medicine.')
      return
    }
    for (const m of meds) {
      if (!m.dosage.trim()) {
        setRxError(`Enter dosage for ${m.name}.`)
        return
      }
      if (!['once', 'as_needed'].includes(m.frequency_pattern) && m.times_per_day < 1) {
        setRxError(`Set how many times per day for ${m.name}.`)
        return
      }
    }
    try {
      await api.createPrescription({
        patient_id: selectedPatient.id,
        disease: rxForm.disease.trim(),
        doctor_notes: rxForm.notes,
        medicines: meds.map(m => ({
          name: m.name.trim(),
          disease: (m.disease || rxForm.disease).trim(),
          dosage: m.dosage.trim(),
          duration_days: m.duration_days,
          frequency_pattern: m.frequency_pattern,
          times_per_day: ['once', 'as_needed'].includes(m.frequency_pattern) ? 1 : m.times_per_day,
        })),
      })
      setRxForm(emptyRxForm(rxForm.disease))
      setRxMsg('Prescription saved. Patient will set start date & time in their portal.')
      api.getPatients().then(setPatients)
    } catch (e) {
      setRxError(e instanceof Error ? e.message : 'Could not save prescription')
    }
  }

  const createSlots = async () => {
    if (!slotForm.slot_date) {
      alert('Please select a date')
      return
    }
    await api.createOPDSlots({ slot_date: slotForm.slot_date, count: 5, duration_minutes: 10 })
    alert('5 slots created (10 minutes each) with video room links!')
    api.getDoctorSlots().then(setSlots)
  }

  return (
    <DashboardLayout title="Doctor Portal" tabs={DoctorTabs} activeTab={tab} onTabChange={setTab}>
      {tab === 'patients' && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card title="My Patients" subtitle={`${patients.length} patients`}>
            <div className="space-y-2">
              {patients.map(p => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPatient(p)}
                  className={`w-full text-left p-3 rounded-xl border transition-all text-slate-900 dark:text-slate-100
                    ${selectedPatient?.id === p.id ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/40' : 'border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                >
                  <div className="flex justify-between">
                    <p className="font-medium text-slate-900 dark:text-slate-100">{p.name}</p>
                    <Badge variant={p.risk_level === 'high' ? 'danger' : p.risk_level === 'medium' ? 'warning' : 'success'}>
                      {p.risk_level}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500">{p.patient_code} · {p.disease || 'No condition'}</p>
                </button>
              ))}
            </div>
          </Card>

          {selectedPatient && (
            <div className="space-y-6">
              <Card title="Vitals at registration">
                <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                  <div><dt className="text-slate-500">Weight</dt><dd>{selectedPatient.weight_kg ?? '—'} kg</dd></div>
                  <div><dt className="text-slate-500">Height</dt><dd>{selectedPatient.height_cm ?? '—'} cm</dd></div>
                  <div><dt className="text-slate-500">Temperature</dt><dd>{selectedPatient.temperature_c ?? '—'} °C</dd></div>
                  <div><dt className="text-slate-500">Pulse</dt><dd>{selectedPatient.pulse_bpm ?? '—'} bpm</dd></div>
                  <div><dt className="text-slate-500">SpO₂</dt><dd>{selectedPatient.oxygen_spo2 ?? '—'}%</dd></div>
                  <div><dt className="text-slate-500">Blood pressure</dt><dd>{selectedPatient.blood_pressure || '—'}</dd></div>
                  <div><dt className="text-slate-500">Blood group</dt><dd>{selectedPatient.blood_group || '—'}</dd></div>
                  <div><dt className="text-slate-500">Contact</dt><dd>{selectedPatient.contact || '—'}</dd></div>
                </dl>
              </Card>

              <Card title={`Prescription — ${selectedPatient.name}`}>
                {rxMsg && <div className="portal-banner-info mb-4">{rxMsg}</div>}
                {rxError && (
                  <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-700 dark:text-red-300">
                    {rxError}
                  </div>
                )}

                <input
                  value={rxForm.disease}
                  onChange={e => setRxForm(f => ({ ...f, disease: e.target.value }))}
                  placeholder="Disease / diagnosis *"
                  className="portal-input w-full mb-4"
                />
                <textarea
                  value={rxForm.notes}
                  onChange={e => setRxForm(f => ({ ...f, notes: e.target.value }))}
                  placeholder="Doctor notes (optional)"
                  className="portal-input w-full mb-4 h-20 resize-none"
                />

                <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">Medicines</h4>
                <div className="space-y-4">
                  {rxForm.medicines.map((m, i) => (
                    <div key={i} className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 space-y-3">
                      <p className="text-xs font-semibold text-slate-500">Medicine {i + 1}</p>
                      <div className="grid sm:grid-cols-2 gap-3">
                        <input
                          placeholder="Medicine name *"
                          value={m.name}
                          onChange={e => updateMedicine(i, { name: e.target.value })}
                          className="portal-input"
                        />
                        <input
                          placeholder="Indication (optional)"
                          value={m.disease}
                          onChange={e => updateMedicine(i, { disease: e.target.value })}
                          className="portal-input"
                        />
                        <input
                          placeholder="Dosage (e.g. 500mg) *"
                          value={m.dosage}
                          onChange={e => updateMedicine(i, { dosage: e.target.value })}
                          className="portal-input"
                        />
                        <input
                          type="number"
                          min={1}
                          max={365}
                          placeholder="Duration (days)"
                          value={m.duration_days}
                          onChange={e => updateMedicine(i, { duration_days: +e.target.value })}
                          className="portal-input"
                        />
                        <select
                          value={m.frequency_pattern}
                          onChange={e => updateMedicine(i, { frequency_pattern: e.target.value as FrequencyPattern })}
                          className="portal-input sm:col-span-2"
                        >
                          {FREQUENCY_OPTIONS.map(o => (
                            <option key={o.value} value={o.value}>{o.label}</option>
                          ))}
                        </select>
                        {!['once', 'as_needed'].includes(m.frequency_pattern) && (
                          <select
                            value={m.times_per_day}
                            onChange={e => updateMedicine(i, { times_per_day: +e.target.value })}
                            className="portal-input sm:col-span-2"
                          >
                            {[1, 2, 3, 4, 5, 6].map(n => (
                              <option key={n} value={n}>{n} time{n > 1 ? 's' : ''} per day</option>
                            ))}
                          </select>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="flex flex-wrap gap-2 mt-4">
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={() => setRxForm(f => ({
                      ...f,
                      medicines: [...f.medicines, { ...defaultMedicineRow(), disease: f.disease }],
                    }))}
                  >
                    + Add medicine
                  </Button>
                  <Button onClick={createPrescription}>Save prescription</Button>
                </div>
              </Card>
            </div>
          )}
        </div>
      )}

      {tab === 'opd' && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card title="Generate OPD Slots" subtitle="Creates 5 consecutive 10-minute slots per click">
            <div className="space-y-3">
              <input
                type="date"
                value={slotForm.slot_date}
                onChange={e => setSlotForm(f => ({ ...f, slot_date: e.target.value }))}
                className="portal-input w-full"
              />
              <Button onClick={createSlots} disabled={!slotForm.slot_date}>Generate 5 Slots</Button>
            </div>
          </Card>

          <Card title="My OPD Slots" subtitle="10-minute blocks · same video room per slot">
            {slots.length === 0 ? (
              <p className="text-slate-500 dark:text-slate-400 text-sm py-4">No slots yet. Create some above.</p>
            ) : slots.map(s => (
              <div key={s.id} className="p-3 portal-surface rounded-xl mb-2">
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <p className="font-medium text-sm text-slate-900 dark:text-slate-100">
                      {s.slot_date} · {s.start_time} – {s.end_time}
                    </p>
                    <p className="text-xs text-primary-600 dark:text-primary-400 mt-0.5">10 min · Room: {s.room}</p>
                    {s.is_booked ? (
                      <span className="mt-1 inline-block"><Badge variant="success">Booked — {s.patient_name}</Badge></span>
                    ) : (
                      <span className="mt-1 inline-block"><Badge variant="default">Open</Badge></span>
                    )}
                  </div>
                </div>
                <VideoCallPanel
                  roomName={s.room}
                  displayName={user?.name ? `Dr. ${user.name}` : 'Doctor'}
                  bookingId={s.booking_id || s.id}
                />
              </div>
            ))}
          </Card>
        </div>
      )}

      {tab === 'summaries' && <ConsultationSummariesPanel />}

      {tab === 'alerts' && (
        <AlertsList
          alerts={alerts}
          role="doctor"
          onResolve={(id) => api.resolveAlert(id).then(() => api.getAlerts().then(setAlerts))}
        />
      )}
    </DashboardLayout>
  )
}
