import { useState, useEffect } from 'react'
import { DashboardLayout, ReceptionTabs } from '../components/Layout'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { api, type Patient, type Doctor } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function ReceptionDashboard() {
  const [tab, setTab] = useState('register')
  const { user } = useAuth()
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [patients, setPatients] = useState<Patient[]>([])
  const [form, setForm] = useState({
    name: '', age: 30, gender: 'Male', contact: '', email: '', disease: '', doctor_id: '',
  })
  const [createdCode, setCreatedCode] = useState('')

  useEffect(() => {
    if (user?.hospital_id) api.getDoctors(user.hospital_id).then(setDoctors).catch(() => {})
    api.getPatients().then(setPatients).catch(() => {})
  }, [user])

  const register = async () => {
    const result = await api.createPatient(form) as { patient_code: string }
    setCreatedCode(result.patient_code)
    api.getPatients().then(setPatients)
  }

  return (
    <DashboardLayout title="Reception" tabs={ReceptionTabs} activeTab={tab} onTabChange={setTab}>
      {tab === 'register' && (
        <Card title="Register New Patient">
          {createdCode && (
            <div className="mb-4 portal-banner-success">
              <p className="font-semibold">Patient registered!</p>
              <p className="text-sm opacity-90">Patient ID: <strong>{createdCode}</strong></p>
            </div>
          )}
          <div className="grid md:grid-cols-2 gap-4">
            <input placeholder="Full Name" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="portal-input" />
            <input type="number" placeholder="Age" value={form.age} onChange={e => setForm(f => ({ ...f, age: +e.target.value }))}
              className="portal-input" />
            <select value={form.gender} onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}
              className="px-4 py-2.5 border border-slate-200 rounded-xl text-sm">
              <option>Male</option><option>Female</option><option>Other</option>
            </select>
            <input placeholder="Contact" value={form.contact} onChange={e => setForm(f => ({ ...f, contact: e.target.value }))}
              className="portal-input" />
            <select value={form.doctor_id} onChange={e => setForm(f => ({ ...f, doctor_id: e.target.value }))}
              className="px-4 py-2.5 border border-slate-200 rounded-xl text-sm md:col-span-2">
              <option value="">Select Doctor</option>
              {doctors.map(d => <option key={d.id} value={d.id}>Dr. {d.name} — {d.specialization}</option>)}
            </select>
          </div>
          <Button onClick={register} className="mt-4" disabled={!form.name || !form.doctor_id}>
            Register Patient
          </Button>
        </Card>
      )}

      {tab === 'patients' && (
        <Card title="Registered Patients">
          <div className="space-y-2">
            {patients.map(p => (
              <div key={p.id} className="flex justify-between p-3 portal-surface rounded-xl">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">{p.name}</p>
                  <p className="text-xs text-slate-500">{p.patient_code} · {p.age}y · {p.gender}</p>
                </div>
                <span className="text-xs text-slate-400">{p.visit_date}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </DashboardLayout>
  )
}
