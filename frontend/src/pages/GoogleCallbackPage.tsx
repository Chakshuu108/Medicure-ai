import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Heart } from 'lucide-react'
import { api } from '../lib/api'
import { setGoogleTokens } from '../lib/googleAuth'
import { useAuth } from '../context/AuthContext'
import { Button } from '../components/ui/Button'

export function GoogleCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login: authLogin } = useAuth()
  const [error, setError] = useState('')
  const [patientCode, setPatientCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleCode, setGoogleCode] = useState<string | null>(null)
  const [googleEmail, setGoogleEmail] = useState('')

  useEffect(() => {
    const code = searchParams.get('code')
    const oauthError = searchParams.get('error')
    if (oauthError) {
      setError('Google sign-in was cancelled or denied.')
      return
    }
    if (!code) {
      setError('Missing Google authorization code.')
      return
    }
    setGoogleCode(code)
  }, [searchParams])

  const completeLogin = async () => {
    if (!googleCode || !patientCode.trim()) {
      setError('Enter your Patient ID from the hospital.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const response = await api.loginPatientGoogle(patientCode.trim(), googleCode)
      const extra = response.extra || {}
      if (extra.google_access_token) {
        setGoogleTokens(
          extra.google_access_token as string,
          extra.google_refresh_token as string | undefined,
        )
      }
      if (extra.google_email) setGoogleEmail(extra.google_email as string)
      authLogin(response)
      navigate('/patient', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Check your Patient ID.')
    } finally {
      setLoading(false)
    }
  }

  if (!googleCode && !error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-primary-950 to-slate-900 px-4">
      <div className="w-full max-w-md bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-primary-500/30 rounded-xl flex items-center justify-center">
            <Heart className="w-5 h-5 text-primary-300" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Patient Sign In</h1>
            <p className="text-sm text-slate-400">Google verified — enter your Patient ID</p>
          </div>
        </div>

        <div className="p-3 mb-5 bg-emerald-500/15 border border-emerald-500/30 rounded-xl text-sm text-emerald-200">
          Google sign-in successful. Calendar access is included automatically.
        </div>

        <label className="block text-sm text-slate-300 mb-2 font-medium">Patient ID</label>
        <input
          value={patientCode}
          onChange={e => setPatientCode(e.target.value.toUpperCase())}
          placeholder="e.g. PAT-DEMO-0001"
          className="w-full px-4 py-3 mb-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 uppercase"
          onKeyDown={e => e.key === 'Enter' && completeLogin()}
        />

        {googleEmail && (
          <p className="text-xs text-slate-400 mb-4">Signed in as {googleEmail}</p>
        )}

        {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

        <Button onClick={completeLogin} loading={loading} className="w-full" size="lg">
          Continue to Patient Portal
        </Button>

        <button type="button" onClick={() => navigate('/')} className="w-full mt-4 text-sm text-slate-400 hover:text-white">
          Back to home
        </button>
      </div>
    </div>
  )
}
