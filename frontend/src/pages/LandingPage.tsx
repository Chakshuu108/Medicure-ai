import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Activity,
  ArrowRight,
  Brain,
  Calendar,
  CheckCircle2,
  ClipboardList,
  Heart,
  LogIn,
  Shield,
  Sparkles,
  Stethoscope,
  Users,
  Video,
  Zap,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Card'
import { api, type DemoCredential } from '../lib/api'
import { useAuth } from '../context/AuthContext'

const features = [
  {
    icon: Brain,
    title: 'Multi-Agent AI',
    desc: 'LangGraph routes your request across specialized clinical agents in real time.',
    color: 'from-violet-500/20 to-purple-500/5 text-violet-300',
  },
  {
    icon: Zap,
    title: 'Live Agent Traces',
    desc: 'Watch orchestration, risk checks, and synthesis happen as you chat.',
    color: 'from-amber-500/20 to-orange-500/5 text-amber-300',
  },
  {
    icon: Video,
    title: 'Video OPD',
    desc: 'Jitsi-powered consultations with AI-generated post-call summaries.',
    color: 'from-cyan-500/20 to-teal-500/5 text-cyan-300',
  },
  {
    icon: Shield,
    title: 'Health Guardian',
    desc: 'Background monitoring detects patterns and alerts doctors proactively.',
    color: 'from-emerald-500/20 to-green-500/5 text-emerald-300',
  },
  {
    icon: Activity,
    title: 'Risk Intelligence',
    desc: 'Clinical risk scoring with narrative insights from patient history.',
    color: 'from-rose-500/20 to-pink-500/5 text-rose-300',
  },
  {
    icon: Calendar,
    title: 'Smart Scheduling',
    desc: 'Book OPD slots, sync meds to Google Calendar, and manage reminders.',
    color: 'from-blue-500/20 to-indigo-500/5 text-blue-300',
  },
]

const stats = [
  { value: '8+', label: 'AI Agents' },
  { value: '4', label: 'Portals' },
  { value: '24/7', label: 'Monitoring' },
  { value: 'HIPAA-ready', label: 'Architecture' },
]

const steps = [
  { step: '01', title: 'Sign in', desc: 'Choose your role — patient, doctor, admin, or reception.' },
  { step: '02', title: 'Connect', desc: 'Book OPD, chat with AI, or manage clinical workflows.' },
  { step: '03', title: 'Consult', desc: 'Join video calls; summaries save automatically for both sides.' },
]

const roleIcons: Record<string, React.ReactNode> = {
  admin: <Users className="w-4 h-4" />,
  doctor: <Stethoscope className="w-4 h-4" />,
  receptionist: <ClipboardList className="w-4 h-4" />,
  patient: <Heart className="w-4 h-4" />,
}

const roleColors: Record<string, string> = {
  patient: 'from-blue-500 to-cyan-500',
  doctor: 'from-violet-500 to-purple-600',
  admin: 'from-slate-500 to-slate-700',
  receptionist: 'from-emerald-500 to-teal-600',
}

export function LandingPage() {
  const navigate = useNavigate()
  const { user, login: authLogin } = useAuth()
  const [demos, setDemos] = useState<DemoCredential[]>([])
  const [selectedRole, setSelectedRole] = useState('patient')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (user) navigate(`/${user.role}`)
    api.getDemoCredentials().then(setDemos).catch(() => {})
  }, [user, navigate])

  const selectDemo = (demo: DemoCredential) => {
    setSelectedRole(demo.role)
    if (demo.role !== 'patient') {
      setEmail(demo.email_or_code)
      setPassword(demo.password || '')
    }
  }

  const login = async () => {
    setLoading(true)
    setError('')
    try {
      let response
      if (selectedRole === 'admin') response = await api.loginAdmin(email, password)
      else if (selectedRole === 'doctor') response = await api.loginDoctor(email, password)
      else if (selectedRole === 'receptionist') response = await api.loginReceptionist(email, password)
      else response = await api.loginPatient(email)
      authLogin(response)
      navigate(`/${response.role}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const scrollToPortals = () => {
    document.getElementById('portals')?.scrollIntoView({ behavior: 'smooth' })
  }

  const portalMeta: Record<string, { desc: string }> = {
    patient: { desc: 'AI chat, video OPD, health checks' },
    doctor: { desc: 'Prescriptions, alerts, consultations' },
    admin: { desc: 'Hospital & staff management' },
    receptionist: { desc: 'Patient registration' },
  }

  return (
    <div className="min-h-screen bg-[#060912] text-white overflow-x-hidden" style={{ fontFamily: 'var(--font-sans)' }}>
      {/* Ambient background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-violet-600/20 blur-[120px]" />
        <div className="absolute top-[30%] right-[-15%] w-[500px] h-[500px] rounded-full bg-cyan-500/15 blur-[100px]" />
        <div className="absolute bottom-[-10%] left-[30%] w-[400px] h-[400px] rounded-full bg-emerald-500/10 blur-[90px]" />
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,.08) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.08) 1px, transparent 1px)',
            backgroundSize: '64px 64px',
          }}
        />
      </div>

      {/* Navbar */}
      <header className="relative z-10 border-b border-white/5 bg-[#060912]/80 backdrop-blur-xl sticky top-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/25">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight" style={{ fontFamily: 'var(--font-display)' }}>
              Medi<span className="text-violet-400">Cure</span>
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm text-slate-400">
            <a href="#portals" className="hover:text-white transition-colors">Portals</a>
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-white transition-colors">How it works</a>
          </nav>
          <Button size="sm" onClick={() => document.getElementById('portals')?.scrollIntoView({ behavior: 'smooth' })} className="shadow-lg shadow-violet-500/20">
            Get Started <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* 4 Portals + Sign In — TOP */}
      <section id="portals" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pt-10 pb-16 lg:pt-14 lg:pb-20">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <div className="text-center mb-8">
            <p className="text-violet-400 text-sm font-semibold uppercase tracking-widest mb-2">Access</p>
            <h1
              className="text-3xl sm:text-4xl font-bold text-white mb-2"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              Choose your portal
            </h1>
            <p className="text-slate-400 text-sm max-w-lg mx-auto">
              Select a role below and sign in. Use two browser tabs to test doctor &amp; patient together.
            </p>
          </div>

          {/* 4 portal cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-8">
            {(['patient', 'doctor', 'admin', 'receptionist'] as const).map(role => (
              <button
                key={role}
                type="button"
                onClick={() => setSelectedRole(role)}
                className={`text-left p-4 sm:p-5 rounded-2xl border transition-all duration-200
                  ${selectedRole === role
                    ? 'bg-violet-600/20 border-violet-500/60 ring-2 ring-violet-400/40 shadow-lg shadow-violet-600/20'
                    : 'bg-white/[0.04] border-white/10 hover:bg-white/[0.08] hover:border-white/20'}`}
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${roleColors[role]} flex items-center justify-center text-white mb-3`}>
                  {roleIcons[role]}
                </div>
                <p className="font-semibold capitalize text-white text-sm sm:text-base" style={{ fontFamily: 'var(--font-display)' }}>
                  {role}
                </p>
                <p className="text-xs text-slate-500 mt-1 leading-snug">{portalMeta[role].desc}</p>
              </button>
            ))}
          </div>

          {/* Sign-in card */}
          <div className="max-w-2xl mx-auto bg-white/[0.04] backdrop-blur-xl border border-white/10 rounded-3xl p-6 sm:p-8 shadow-2xl shadow-black/20">
            <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2" style={{ fontFamily: 'var(--font-display)' }}>
              <LogIn className="w-5 h-5 text-violet-400" />
              Sign in as <span className="capitalize text-violet-300">{selectedRole}</span>
            </h3>
            <p className="text-slate-500 text-sm mb-5">Quick demo credentials</p>

            <div className="space-y-2 mb-5">
              {demos.map(demo => (
                <button
                  key={demo.role}
                  type="button"
                  onClick={() => selectDemo(demo)}
                  className={`w-full text-left px-4 py-3 rounded-xl border transition-all text-sm
                    ${selectedRole === demo.role
                      ? 'border-violet-500/60 bg-violet-500/10 text-white'
                      : 'border-white/8 bg-white/[0.02] text-slate-400 hover:bg-white/5 hover:text-slate-200'}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium capitalize">{demo.role}</span>
                    <Badge variant="info">{demo.email_or_code}</Badge>
                  </div>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-1">{demo.description}</p>
                </button>
              ))}
            </div>

            {selectedRole === 'patient' ? (
              <div className="space-y-4 pt-2 border-t border-white/8">
                <p className="text-sm text-slate-400">
                  Sign in with Google, then enter Patient ID{' '}
                  <code className="text-violet-300 bg-violet-500/10 px-1.5 py-0.5 rounded">PAT-DEMO-0001</code>
                </p>
                {error && <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>}
                <button
                  type="button"
                  disabled={loading}
                  onClick={async () => {
                    setLoading(true)
                    setError('')
                    try {
                      const { url } = await api.getGoogleAuthUrl('patient_login')
                      window.location.href = url
                    } catch (e) {
                      setError(e instanceof Error ? e.message : 'Google sign-in unavailable')
                      setLoading(false)
                    }
                  }}
                  className="w-full flex items-center justify-center gap-3 px-6 py-3.5 bg-white text-slate-800 rounded-xl font-semibold text-sm hover:bg-slate-100 transition-colors disabled:opacity-50 shadow-lg"
                >
                  {loading ? (
                    <span className="w-5 h-5 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                    </svg>
                  )}
                  Continue with Google
                </button>
              </div>
            ) : (
              <div className="space-y-3 pt-2 border-t border-white/8">
                <input
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="Email"
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 transition-all"
                />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Password"
                  onKeyDown={e => e.key === 'Enter' && login()}
                  className="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500/50 transition-all"
                />
                {error && <p className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</p>}
                <Button onClick={login} loading={loading} className="w-full !py-3.5 shadow-lg shadow-violet-600/25" size="lg">
                  Sign in as {selectedRole}
                </Button>
              </div>
            )}
          </div>
        </motion.div>
      </section>

      {/* Hero */}
      <section className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pt-8 pb-16 lg:pb-20 border-t border-white/5">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 bg-white/5 border border-white/10 rounded-full px-4 py-1.5 text-sm text-violet-300 mb-8">
              <Sparkles className="w-4 h-4" />
              Agentic AI Healthcare Platform v3.0
            </div>
            <h2
              className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.1] tracking-tight mb-6"
              style={{ fontFamily: 'var(--font-display)' }}
            >
              Healthcare that{' '}
              <span className="bg-gradient-to-r from-violet-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
                thinks with you
              </span>
            </h2>
            <p className="text-lg text-slate-400 leading-relaxed max-w-xl mb-8">
              MediCure connects patients and doctors through AI agents, video OPD,
              smart alerts, and automated consultation summaries — all in one platform.
            </p>
            <div className="flex flex-wrap gap-3 mb-10">
              <Button size="lg" onClick={scrollToPortals} className="shadow-xl shadow-violet-600/30">
                Launch Portal <ArrowRight className="w-4 h-4" />
              </Button>
              <a href="#features">
                <Button size="lg" variant="secondary" className="!bg-white/5 !border-white/10 !text-white hover:!bg-white/10">
                  Explore features
                </Button>
              </a>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {stats.map(s => (
                <div key={s.label} className="p-3 rounded-2xl bg-white/5 border border-white/8">
                  <p className="text-xl font-bold text-white" style={{ fontFamily: 'var(--font-display)' }}>{s.value}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Hero visual */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="relative hidden lg:block"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-violet-500/20 to-cyan-500/10 rounded-3xl blur-2xl" />
            <div className="relative bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-sm shadow-2xl">
              <div className="flex items-center gap-2 mb-5 pb-4 border-b border-white/10">
                <div className="w-3 h-3 rounded-full bg-red-400/80" />
                <div className="w-3 h-3 rounded-full bg-amber-400/80" />
                <div className="w-3 h-3 rounded-full bg-emerald-400/80" />
                <span className="ml-2 text-xs text-slate-500">MediCure Agent Console</span>
              </div>
              <div className="space-y-3">
                {['Orchestrator', 'Conversation Agent', 'Risk Assessment', 'Response Synthesizer'].map((agent, i) => (
                  <motion.div
                    key={agent}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 + i * 0.12 }}
                    className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/8"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span className="text-sm text-slate-300">{agent}</span>
                    <span className="ml-auto text-xs text-slate-600">completed</span>
                  </motion.div>
                ))}
              </div>
              <div className="mt-5 p-4 rounded-xl bg-gradient-to-r from-violet-500/15 to-cyan-500/10 border border-violet-500/20">
                <p className="text-xs text-violet-300 font-medium mb-1">AI Response</p>
                <p className="text-sm text-slate-300 leading-relaxed">
                  Your symptoms suggest mild tension. I've noted your medications and scheduled a follow-up reminder.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-20">
        <div className="text-center mb-14">
          <p className="text-violet-400 text-sm font-semibold uppercase tracking-widest mb-3">Platform</p>
          <h2 className="text-3xl sm:text-4xl font-bold" style={{ fontFamily: 'var(--font-display)' }}>
            Everything clinical teams need
          </h2>
          <p className="text-slate-400 mt-3 max-w-xl mx-auto">
            From AI triage to video consultations — built for modern healthcare workflows.
          </p>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.06 }}
              className="group p-6 rounded-2xl bg-white/[0.03] border border-white/8 hover:border-white/15 hover:bg-white/[0.06] transition-all duration-300"
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <f.icon className="w-6 h-6" />
              </div>
              <h3 className="font-semibold text-white text-lg mb-2" style={{ fontFamily: 'var(--font-display)' }}>{f.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 py-20">
        <div className="rounded-3xl bg-gradient-to-br from-white/[0.06] to-white/[0.02] border border-white/10 p-8 sm:p-12">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)' }}>How it works</h2>
            <p className="text-slate-400 mt-2">Three steps to a smarter consultation</p>
          </div>
          <div className="grid md:grid-cols-3 gap-10 md:gap-6 max-w-5xl mx-auto">
            {steps.map((s, i) => (
              <div key={s.step} className="relative flex flex-col items-center text-center md:px-4">
                {i < steps.length - 1 && (
                  <div
                    className="hidden md:block absolute top-7 left-[calc(50%+2.5rem)] w-[calc(100%-5rem)] h-px bg-gradient-to-r from-violet-500/50 via-violet-400/30 to-transparent pointer-events-none"
                    aria-hidden
                  />
                )}
                <div
                  className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600/40 to-indigo-600/20 border border-violet-400/30 flex items-center justify-center mb-5 shrink-0"
                  style={{ fontFamily: 'var(--font-display)' }}
                >
                  <span className="text-lg font-bold text-violet-200">{s.step}</span>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed max-w-xs">{s.desc}</p>
              </div>
            ))}
          </div>
          <p className="text-center text-xs text-slate-500 mt-12 max-w-lg mx-auto">
            Tip: open doctor and patient portals in <strong className="text-slate-400">two separate browser tabs</strong> to test video OPD side by side.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 bg-[#04060d]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm">
            <Heart className="w-4 h-4 text-violet-500" />
            <span>MediCure AI — Agentic Healthcare Platform</span>
          </div>
          <p className="text-xs text-slate-600">Built with LangGraph · FastAPI · React · PostgreSQL</p>
        </div>
      </footer>
    </div>
  )
}
