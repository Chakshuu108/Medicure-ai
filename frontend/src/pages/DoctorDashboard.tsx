import { useState, useEffect } from 'react'

import { DashboardLayout, DoctorTabs } from '../components/Layout'

import { VideoCallPanel } from '../components/VideoCallPanel'

import { AlertsList } from '../components/AlertsList'

import { ConsultationSummariesPanel } from '../components/ConsultationSummariesPanel'

import { Card, Badge } from '../components/ui/Card'

import { Button } from '../components/ui/Button'

import { api, type Patient, type Alert, type DoctorSlot } from '../lib/api'

import { useAuth } from '../context/AuthContext'



export function DoctorDashboard() {

  const [tab, setTab] = useState('patients')

  const { user } = useAuth()

  const [patients, setPatients] = useState<Patient[]>([])

  const [alerts, setAlerts] = useState<Alert[]>([])

  const [slots, setSlots] = useState<DoctorSlot[]>([])

  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)

  const [rxForm, setRxForm] = useState({ notes: '', medicines: [{ name: '', dosage: '', timing: 'morning', duration_days: 7 }] })

  const [slotForm, setSlotForm] = useState({ slot_date: '' })



  useEffect(() => {

    api.getPatients().then(setPatients).catch(() => {})

    if (tab === 'alerts') api.getAlerts().then(setAlerts).catch(() => {})

    if (tab === 'opd') api.getDoctorSlots().then(setSlots).catch(() => {})

  }, [tab])



  const createPrescription = async () => {

    if (!selectedPatient) return

    await api.createPrescription({

      patient_id: selectedPatient.id,

      doctor_notes: rxForm.notes,

      medicines: rxForm.medicines.filter(m => m.name),

    })

    setRxForm({ notes: '', medicines: [{ name: '', dosage: '', timing: 'morning', duration_days: 7 }] })

    alert('Prescription created!')

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

                <button key={p.id} onClick={() => setSelectedPatient(p)}

                  className={`w-full text-left p-3 rounded-xl border transition-all text-slate-900 dark:text-slate-100
                    ${selectedPatient?.id === p.id ? 'border-primary-500 bg-primary-50 dark:bg-primary-950/40' : 'border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800'}`}>

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

            <Card title={`Prescribe for ${selectedPatient.name}`}>

              <textarea value={rxForm.notes} onChange={e => setRxForm(f => ({ ...f, notes: e.target.value }))}

                placeholder="Doctor notes..." className="portal-input w-full mb-4 h-20 resize-none" />

              {rxForm.medicines.map((m, i) => (

                <div key={i} className="grid grid-cols-2 gap-2 mb-2">

                  <input placeholder="Medicine" value={m.name} onChange={e => {

                    const meds = [...rxForm.medicines]; meds[i].name = e.target.value; setRxForm(f => ({ ...f, medicines: meds }))

                  }} className="portal-input px-3 py-2 rounded-lg" />

                  <input placeholder="Dosage" value={m.dosage} onChange={e => {

                    const meds = [...rxForm.medicines]; meds[i].dosage = e.target.value; setRxForm(f => ({ ...f, medicines: meds }))

                  }} className="portal-input px-3 py-2 rounded-lg" />

                </div>

              ))}

              <div className="flex gap-2 mt-4">

                <Button size="sm" variant="secondary" onClick={() => setRxForm(f => ({ ...f, medicines: [...f.medicines, { name: '', dosage: '', timing: 'morning', duration_days: 7 }] }))}>

                  + Add Medicine

                </Button>

                <Button onClick={createPrescription}>Save Prescription</Button>

              </div>

            </Card>

          )}

        </div>

      )}



      {tab === 'opd' && (

        <div className="grid md:grid-cols-2 gap-6">

          <Card title="Generate OPD Slots" subtitle="Creates 5 consecutive 10-minute slots per click">

            <div className="space-y-3">

              <input type="date" value={slotForm.slot_date} onChange={e => setSlotForm(f => ({ ...f, slot_date: e.target.value }))}

                className="portal-input w-full" />

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

                    <p className="font-medium text-sm text-slate-900 dark:text-slate-100">{s.slot_date} · {s.start_time} – {s.end_time}</p>

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


