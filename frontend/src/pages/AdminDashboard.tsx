import { useState } from 'react'
import { DashboardLayout, AdminTabs } from '../components/Layout'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { api } from '../lib/api'

export function AdminDashboard() {
  const [tab, setTab] = useState('doctors')
  const [doctorForm, setDoctorForm] = useState({ name: '', email: '', password: 'demo123', specialization: 'General Medicine' })
  const [recForm, setRecForm] = useState({ name: '', email: '', password: 'demo123' })
  const [msg, setMsg] = useState('')

  const addDoctor = async () => {
    await api.createDoctor(doctorForm)
    setMsg('Doctor added successfully!')
    setDoctorForm({ name: '', email: '', password: 'demo123', specialization: 'General Medicine' })
  }

  const addReceptionist = async () => {
    await api.createReceptionist(recForm)
    setMsg('Receptionist added!')
  }

  return (
    <DashboardLayout title="Hospital Admin" tabs={AdminTabs} activeTab={tab} onTabChange={setTab}>
      {msg && <div className="portal-banner-info">{msg}</div>}

      {tab === 'doctors' && (
        <Card title="Add Doctor">
          <div className="grid md:grid-cols-2 gap-4">
            {(['name', 'email', 'password', 'specialization'] as const).map(field => (
              <input key={field} placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
                value={doctorForm[field]} onChange={e => setDoctorForm(f => ({ ...f, [field]: e.target.value }))}
                className="portal-input" />
            ))}
          </div>
          <Button onClick={addDoctor} className="mt-4">Add Doctor</Button>
        </Card>
      )}

      {tab === 'staff' && (
        <Card title="Add Receptionist">
          <div className="grid md:grid-cols-2 gap-4">
            {(['name', 'email', 'password'] as const).map(field => (
              <input key={field} placeholder={field.charAt(0).toUpperCase() + field.slice(1)}
                value={recForm[field]} onChange={e => setRecForm(f => ({ ...f, [field]: e.target.value }))}
                className="portal-input" />
            ))}
          </div>
          <Button onClick={addReceptionist} className="mt-4">Add Receptionist</Button>
        </Card>
      )}
    </DashboardLayout>
  )
}
