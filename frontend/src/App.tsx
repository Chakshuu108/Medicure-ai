import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { AgentActivityProvider } from './context/AgentActivityContext'
import { AgentActivityPanel } from './components/AgentActivityPanel'
import { LandingPage } from './pages/LandingPage'
import { PatientDashboard } from './pages/PatientDashboard'
import { DoctorDashboard } from './pages/DoctorDashboard'
import { AdminDashboard } from './pages/AdminDashboard'
import { ReceptionDashboard } from './pages/ReceptionDashboard'
import { GoogleCallbackPage } from './pages/GoogleCallbackPage'

function ProtectedRoute({ children, role }: { children: React.ReactNode; role?: string }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950"><div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" /></div>
  if (!user) return <Navigate to="/" />
  if (role && user.role !== role) return <Navigate to={`/${user.role}`} />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/patient" element={<ProtectedRoute role="patient"><PatientDashboard /></ProtectedRoute>} />
      <Route path="/auth/google/callback" element={<GoogleCallbackPage />} />
      <Route path="/doctor" element={<ProtectedRoute role="doctor"><DoctorDashboard /></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute role="admin"><AdminDashboard /></ProtectedRoute>} />
      <Route path="/receptionist" element={<ProtectedRoute role="receptionist"><ReceptionDashboard /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <AgentActivityProvider>
            <AppRoutes />
            <AgentActivityPanel />
          </AgentActivityProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  )
}
