import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, AlertTriangle, Calendar, ClipboardList, Heart, LogOut, MessageSquare, Shield, Stethoscope, Users } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Button } from './ui/Button'
import { Badge } from './ui/Card'
import { ThemeToggle } from './ThemeToggle'
import { api } from '../lib/api'

interface LayoutProps {
  children: React.ReactNode
  title: string
  tabs?: { id: string; label: string; icon: React.ReactNode }[]
  activeTab?: string
  onTabChange?: (id: string) => void
}

export function DashboardLayout({ children, tabs, activeTab, onTabChange }: LayoutProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [alertCount, setAlertCount] = useState(0)

  useEffect(() => {
    api.getAlerts().then(alerts => setAlertCount(alerts.filter(a => !a.resolved).length)).catch(() => {})
  }, [])

  const roleColors: Record<string, string> = {
    patient: 'from-blue-600 to-cyan-600',
    doctor: 'from-primary-600 to-violet-600',
    admin: 'from-slate-700 to-slate-900',
    receptionist: 'from-emerald-600 to-teal-600',
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
      {/* Top nav */}
      <header className={`bg-gradient-to-r ${roleColors[user?.role || 'patient']} text-white shadow-lg`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
              <Heart className="w-5 h-5" />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight">MediCure AI</h1>
              <p className="text-xs text-white/70 capitalize">{user?.role} Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle className="text-white hover:bg-white/20" />
            <div className="hidden md:block text-right text-white/90 text-sm font-medium px-3 py-1.5 rounded-lg bg-white/10">
              {new Date().toLocaleDateString('en-IN', {
                weekday: 'short',
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              })}
            </div>
            {alertCount > 0 && (
              <Badge variant="danger">
                <AlertTriangle className="w-3 h-3 mr-1" />
                {alertCount} alerts
              </Badge>
            )}
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium">{user?.name}</p>
              {user?.patient_code && <p className="text-xs text-white/70">{user.patient_code}</p>}
            </div>
            <Button variant="ghost" size="sm" onClick={() => { logout(); navigate('/') }}
              className="text-white hover:bg-white/20 border-0">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
        {tabs && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 flex gap-1 overflow-x-auto pb-0">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => onTabChange?.(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-xl transition-all whitespace-nowrap
                  ${activeTab === tab.id
                    ? 'bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-white'
                    : 'text-white/80 hover:text-white hover:bg-white/10'}`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        )}
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
          {children}
        </motion.div>
      </main>
    </div>
  )
}

export const PatientTabs = [
  { id: 'chat', label: 'AI Assistant', icon: <MessageSquare className="w-4 h-4" /> },
  { id: 'care', label: 'Schedule & Prescriptions', icon: <Calendar className="w-4 h-4" /> },
  { id: 'health', label: 'Health Check', icon: <Activity className="w-4 h-4" /> },
  { id: 'alerts', label: 'Alerts', icon: <AlertTriangle className="w-4 h-4" /> },
  { id: 'opd', label: 'OPD Booking', icon: <Calendar className="w-4 h-4" /> },
  { id: 'summaries', label: 'Consultation Summaries', icon: <ClipboardList className="w-4 h-4" /> },
  { id: 'guardian', label: 'Health Guardian', icon: <Shield className="w-4 h-4" /> },
]

export const DoctorTabs = [
  { id: 'patients', label: 'Patients', icon: <Users className="w-4 h-4" /> },
  { id: 'prescriptions', label: 'Prescriptions', icon: <ClipboardList className="w-4 h-4" /> },
  { id: 'opd', label: 'OPD Management', icon: <Calendar className="w-4 h-4" /> },
  { id: 'summaries', label: 'Consultation Summaries', icon: <ClipboardList className="w-4 h-4" /> },
  { id: 'alerts', label: 'Alerts', icon: <AlertTriangle className="w-4 h-4" /> },
]

export const AdminTabs = [
  { id: 'hospital', label: 'Hospital', icon: <Heart className="w-4 h-4" /> },
  { id: 'doctors', label: 'Doctors', icon: <Stethoscope className="w-4 h-4" /> },
  { id: 'staff', label: 'Receptionists', icon: <Users className="w-4 h-4" /> },
]

export const ReceptionTabs = [
  { id: 'register', label: 'Register Patient', icon: <Users className="w-4 h-4" /> },
  { id: 'patients', label: 'Today\'s Patients', icon: <ClipboardList className="w-4 h-4" /> },
]
