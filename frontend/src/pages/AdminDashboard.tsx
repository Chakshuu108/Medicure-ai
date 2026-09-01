import { useCallback, useEffect, useState } from 'react'
import { DashboardLayout, AdminTabs } from '../components/Layout'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { api, type HospitalDoctor, type HospitalProfile, type HospitalReceptionist } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function AdminDashboard() {
  const { user } = useAuth()
  const [tab, setTab] = useState('hospital')
  const [hospital, setHospital] = useState<HospitalProfile | null>(null)
  const [doctors, setDoctors] = useState<HospitalDoctor[]>([])
  const [receptionists, setReceptionists] = useState<HospitalReceptionist[]>([])
  const [doctorForm, setDoctorForm] = useState({ name: '', email: '', password: '', specialization: 'General Medicine' })
  const [recForm, setRecForm] = useState({ name: '', email: '', password: '' })
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const loadStaff = useCallback(async () => {
    const [h, d, r] = await Promise.all([
      api.getHospital(),
      api.getHospitalDoctors(),
      api.getHospitalReceptionists(),
    ])
    setHospital(h)
    setDoctors(d)
    setReceptionists(r)
  }, [])

  useEffect(() => {
    loadStaff().catch(() => setError('Could not load hospital staff. Check that the API is connected.'))
  }, [loadStaff])

  const addDoctor = async () => {
    setSaving(true)
    setError('')
    setMsg('')
    try {
      await api.createDoctor(doctorForm)
      setMsg(`${doctorForm.name} can now sign in on the Doctor portal with ${doctorForm.email}.`)
      setDoctorForm({ name: '', email: '', password: '', specialization: 'General Medicine' })
      await loadStaff()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not add doctor')
    } finally {
      setSaving(false)
    }
  }

  const addReceptionist = async () => {
    setSaving(true)
    setError('')
    setMsg('')
    try {
      await api.createReceptionist(recForm)
      setMsg(`${recForm.name} can now sign in on the Receptionist portal with ${recForm.email}.`)
      setRecForm({ name: '', email: '', password: '' })
      await loadStaff()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not add receptionist')
    } finally {
      setSaving(false)
    }
  }

  return (
    <DashboardLayout title="Hospital Admin" tabs={AdminTabs} activeTab={tab} onTabChange={setTab}>
      {msg && <div className="portal-banner-info">{msg}</div>}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {tab === 'hospital' && (
        <Card title="Your hospital">
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
            Hospital is registered. Next: add doctors, then receptionists. They sign in on their own portals with the emails you create here.
          </p>
          <dl className="grid sm:grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-slate-500">Hospital</dt>
              <dd className="font-semibold">{hospital?.name || user?.name}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Hospital code</dt>
              <dd className="font-mono">{hospital?.hospital_code || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Admin email</dt>
              <dd>{hospital?.email || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">City</dt>
              <dd>{hospital?.city || '—'}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-slate-500">Address</dt>
              <dd>{hospital?.address || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Phone</dt>
              <dd>{hospital?.phone || '—'}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Staff</dt>
              <dd>
                {doctors.length} doctor{doctors.length === 1 ? '' : 's'} · {receptionists.length} receptionist
                {receptionists.length === 1 ? '' : 's'}
              </dd>
            </div>
          </dl>
        </Card>
      )}

      {tab === 'doctors' && (
        <div className="space-y-6">
          <Card title="Doctors at this hospital">
            {doctors.length === 0 ? (
              <p className="text-sm text-slate-500">No doctors yet. Add the first doctor below — they cannot sign in until you create them.</p>
            ) : (
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {doctors.map(d => (
                  <li key={d.id} className="py-3 flex flex-wrap justify-between gap-2 text-sm">
                    <span className="font-medium">{d.name}</span>
                    <span className="text-slate-500">{d.specialization}</span>
                    <span className="text-slate-500">{d.email}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
          <Card title="Add doctor">
            <div className="grid md:grid-cols-2 gap-4">
              {(['name', 'email', 'password', 'specialization'] as const).map(field => (
                <input
                  key={field}
                  type={field === 'password' ? 'password' : 'text'}
                  placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
                  value={doctorForm[field]}
                  onChange={e => setDoctorForm(f => ({ ...f, [field]: e.target.value }))}
                  className="portal-input"
                />
              ))}
            </div>
            <Button
              onClick={addDoctor}
              loading={saving}
              disabled={!doctorForm.name || !doctorForm.email || !doctorForm.password}
              className="mt-4"
            >
              Add Doctor
            </Button>
          </Card>
        </div>
      )}

      {tab === 'staff' && (
        <div className="space-y-6">
          <Card title="Receptionists at this hospital">
            {receptionists.length === 0 ? (
              <p className="text-sm text-slate-500">No receptionists yet. Add staff after doctors so they can register patients.</p>
            ) : (
              <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                {receptionists.map(r => (
                  <li key={r.id} className="py-3 flex flex-wrap justify-between gap-2 text-sm">
                    <span className="font-medium">{r.name}</span>
                    <span className="text-slate-500">{r.email}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
          <Card title="Add receptionist">
            <div className="grid md:grid-cols-2 gap-4">
              {(['name', 'email', 'password'] as const).map(field => (
                <input
                  key={field}
                  type={field === 'password' ? 'password' : 'text'}
                  placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
                  value={recForm[field]}
                  onChange={e => setRecForm(f => ({ ...f, [field]: e.target.value }))}
                  className="portal-input"
                />
              ))}
            </div>
            <Button
              onClick={addReceptionist}
              loading={saving}
              disabled={!recForm.name || !recForm.email || !recForm.password}
              className="mt-4"
            >
              Add Receptionist
            </Button>
          </Card>
        </div>
      )}
    </DashboardLayout>
  )
}
