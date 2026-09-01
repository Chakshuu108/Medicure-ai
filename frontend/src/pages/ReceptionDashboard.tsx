import { useState, useEffect } from 'react'
import { DashboardLayout, ReceptionTabs } from '../components/Layout'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { api, type Patient, type Doctor } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const BLOOD_GROUPS = ['A+', 'A−', 'B+', 'B−', 'AB+', 'AB−', 'O+', 'O−', 'Unknown'] as const

const emptyForm = () => ({
  name: '',
  age: 30,
  gender: 'Male',
  contact: '',
  email: '',
  disease: '',
  visit_date: new Date().toISOString().slice(0, 10),
  doctor_id: '',
  blood_group: '',
  weight_kg: '',
  height_cm: '',
  temperature_c: '',
  pulse_bpm: '',
  oxygen_spo2: '',
  blood_pressure: '',
  address: '',
})

function formatVitals(p: Patient): string {
  const parts: string[] = []
  if (p.weight_kg != null) parts.push(`${p.weight_kg} kg`)
  if (p.height_cm != null) parts.push(`${p.height_cm} cm`)
  if (p.temperature_c != null) parts.push(`${p.temperature_c}°C`)
  if (p.pulse_bpm != null) parts.push(`${p.pulse_bpm} bpm`)
  if (p.oxygen_spo2 != null) parts.push(`SpO₂ ${p.oxygen_spo2}%`)
  if (p.blood_pressure) parts.push(`BP ${p.blood_pressure}`)
  if (p.blood_group) parts.push(p.blood_group)
  return parts.join(' · ') || 'No vitals recorded'
}

export function ReceptionDashboard() {
  const [tab, setTab] = useState('register')
  const { user } = useAuth()
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [patients, setPatients] = useState<Patient[]>([])
  const [form, setForm] = useState(emptyForm)
  const [createdCode, setCreatedCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user?.hospital_id) api.getDoctors(user.hospital_id).then(setDoctors).catch(() => {})
    api.getPatients().then(setPatients).catch(() => {})
  }, [user])

  const register = async () => {
    setError('')
    const weight = parseFloat(form.weight_kg)
    const height = parseFloat(form.height_cm)
    const temp = parseFloat(form.temperature_c)
    const pulse = parseInt(form.pulse_bpm, 10)
    const spo2 = parseFloat(form.oxygen_spo2)

    if (!form.name.trim()) return setError('Full name is required.')
    if (!form.contact.trim()) return setError('Contact number is required.')
    if (!form.doctor_id) return setError('Select the attending doctor.')
    if (!form.blood_group) return setError('Blood group is required.')
    if (!Number.isFinite(weight) || weight <= 0) return setError('Enter weight in kg.')
    if (!Number.isFinite(height) || height <= 0) return setError('Enter height in cm.')
    if (!Number.isFinite(temp) || temp <= 0) return setError('Enter temperature in °C.')
    if (!Number.isInteger(pulse) || pulse <= 0) return setError('Enter pulse in bpm.')
    if (!Number.isFinite(spo2) || spo2 <= 0 || spo2 > 100) return setError('Enter SpO₂ between 1 and 100.')
    if (!form.blood_pressure.trim()) return setError('Blood pressure is required (e.g. 120/80).')

    setLoading(true)
    try {
      const result = await api.createPatient({
        name: form.name.trim(),
        age: form.age,
        gender: form.gender,
        contact: form.contact.trim(),
        email: form.email.trim(),
        disease: form.disease.trim(),
        visit_date: form.visit_date,
        doctor_id: form.doctor_id,
        blood_group: form.blood_group,
        weight_kg: weight,
        height_cm: height,
        temperature_c: temp,
        pulse_bpm: pulse,
        oxygen_spo2: spo2,
        blood_pressure: form.blood_pressure.trim(),
        address: form.address.trim(),
      }) as { patient_code: string }
      setCreatedCode(result.patient_code)
      setForm(emptyForm())
      api.getPatients().then(setPatients)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <DashboardLayout title="Reception" tabs={ReceptionTabs} activeTab={tab} onTabChange={setTab}>
      {tab === 'register' && (
        <Card title="Register New Patient">
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
            Record patient details and vitals at check-in. All vitals are required before registration.
          </p>
          {createdCode && (
            <div className="mb-4 portal-banner-success">
              <p className="font-semibold">Patient registered!</p>
              <p className="text-sm opacity-90">Patient ID: <strong>{createdCode}</strong></p>
            </div>
          )}
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">Patient details</h4>
          <div className="grid md:grid-cols-2 gap-4 mb-6">
            <input placeholder="Full name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="portal-input" />
            <input type="number" placeholder="Age *" value={form.age} onChange={e => setForm(f => ({ ...f, age: +e.target.value }))}
              className="portal-input" />
            <select value={form.gender} onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}
              className="portal-input">
              <option>Male</option><option>Female</option><option>Other</option><option>Prefer not to say</option>
            </select>
            <input placeholder="Contact number *" value={form.contact} onChange={e => setForm(f => ({ ...f, contact: e.target.value }))}
              className="portal-input" />
            <input type="email" placeholder="Email (optional)" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className="portal-input" />
            <input type="date" value={form.visit_date} onChange={e => setForm(f => ({ ...f, visit_date: e.target.value }))}
              className="portal-input" />
            <input placeholder="Reason for visit (optional)" value={form.disease} onChange={e => setForm(f => ({ ...f, disease: e.target.value }))}
              className="portal-input md:col-span-2" />
            <select value={form.doctor_id} onChange={e => setForm(f => ({ ...f, doctor_id: e.target.value }))}
              className="portal-input md:col-span-2">
              <option value="">Select attending doctor *</option>
              {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.name} — {d.specialization}</option>)}
            </select>
          </div>

          <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">Vitals (required)</h4>
          <div className="grid md:grid-cols-3 gap-4 mb-4">
            <select value={form.blood_group} onChange={e => setForm(f => ({ ...f, blood_group: e.target.value }))}
              className="portal-input">
              <option value="">Blood group *</option>
              {BLOOD_GROUPS.map(bg => <option key={bg} value={bg}>{bg}</option>)}
            </select>
            <input type="number" step="0.1" placeholder="Weight (kg) *" value={form.weight_kg}
              onChange={e => setForm(f => ({ ...f, weight_kg: e.target.value }))} className="portal-input" />
            <input type="number" step="0.1" placeholder="Height (cm) *" value={form.height_cm}
              onChange={e => setForm(f => ({ ...f, height_cm: e.target.value }))} className="portal-input" />
            <input type="number" step="0.1" placeholder="Temperature (°C) *" value={form.temperature_c}
              onChange={e => setForm(f => ({ ...f, temperature_c: e.target.value }))} className="portal-input" />
            <input type="number" placeholder="Pulse (bpm) *" value={form.pulse_bpm}
              onChange={e => setForm(f => ({ ...f, pulse_bpm: e.target.value }))} className="portal-input" />
            <input type="number" step="0.1" placeholder="SpO₂ (%) *" value={form.oxygen_spo2}
              onChange={e => setForm(f => ({ ...f, oxygen_spo2: e.target.value }))} className="portal-input" />
            <input placeholder="Blood pressure (e.g. 120/80) *" value={form.blood_pressure}
              onChange={e => setForm(f => ({ ...f, blood_pressure: e.target.value }))} className="portal-input md:col-span-2" />
          </div>
          <textarea placeholder="Address (optional)" value={form.address} rows={2}
            onChange={e => setForm(f => ({ ...f, address: e.target.value }))}
            className="portal-input w-full mb-4 resize-none" />

          <Button onClick={register} loading={loading} className="mt-2" disabled={!form.name || !form.doctor_id}>
            Register Patient
          </Button>
        </Card>
      )}

      {tab === 'patients' && (
        <Card title="Registered Patients">
          <div className="space-y-3">
            {patients.length === 0 ? (
              <p className="text-sm text-slate-500">No patients registered yet.</p>
            ) : patients.map(p => (
              <div key={p.id} className="p-3 portal-surface rounded-xl">
                <div className="flex flex-wrap justify-between gap-2 mb-1">
                  <div>
                    <p className="font-medium text-slate-900 dark:text-slate-100">{p.name}</p>
                    <p className="text-xs text-slate-500">{p.patient_code} · {p.age}y · {p.gender}</p>
                  </div>
                  <span className="text-xs text-slate-400">{p.visit_date}</span>
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400">{formatVitals(p)}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </DashboardLayout>
  )
}
