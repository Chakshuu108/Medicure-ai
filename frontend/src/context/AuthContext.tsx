import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import type { AuthResponse } from '../lib/api'
import { getUser, saveAuth, clearAuth, type User } from '../lib/utils'
import { setGoogleTokens, clearGoogleTokens } from '../lib/googleAuth'

interface AuthState {
  user: User | null
  loading: boolean
  login: (response: AuthResponse) => void
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const stored = getUser()
    if (stored) setUser(stored)
    setLoading(false)
  }, [])

  const login = (response: AuthResponse) => {
    const u: User = {
      role: response.role,
      id: response.user_id,
      name: response.name,
      token: response.access_token,
      hospital_id: response.hospital_id,
      patient_code: response.extra?.patient_code as string,
      extra: response.extra,
    }
    saveAuth(u)
    setUser(u)
    if (response.role === 'patient' && response.extra) {
      const access = response.extra.google_access_token as string | undefined
      const refresh = response.extra.google_refresh_token as string | undefined
      if (access) setGoogleTokens(access, refresh)
    }
  }

  const logout = () => {
    clearAuth()
    clearGoogleTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
