const ACCESS_KEY = 'google_access_token'
const REFRESH_KEY = 'google_refresh_token'

export function getGoogleAccessToken(): string | null {
  return sessionStorage.getItem(ACCESS_KEY)
}

export function getGoogleRefreshToken(): string | null {
  return sessionStorage.getItem(REFRESH_KEY)
}

export function setGoogleTokens(accessToken: string, refreshToken?: string | null) {
  sessionStorage.setItem(ACCESS_KEY, accessToken)
  if (refreshToken) sessionStorage.setItem(REFRESH_KEY, refreshToken)
}

export function clearGoogleTokens() {
  sessionStorage.removeItem(ACCESS_KEY)
  sessionStorage.removeItem(REFRESH_KEY)
}
