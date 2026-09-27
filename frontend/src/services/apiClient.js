import { demoResponse } from './demoApi'

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')
const demoMode = import.meta.env.VITE_DEMO_MODE === 'true'

function errorMessage(detail, fallback) {
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const messages = detail.map((item) => {
      const field = Array.isArray(item?.loc) ? item.loc.at(-1) : ''
      return [field, item?.msg].filter(Boolean).join(': ')
    }).filter(Boolean)
    if (messages.length) return messages.join('; ')
  }
  return fallback
}

export async function apiRequest(path, options = {}) {
  if (demoMode) return demoResponse(path, options)
  const token = sessionStorage.getItem('bhoomiguard_access_token')
  let response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new Error('BhoomiGuard API is unavailable. Start the FastAPI server and configure its PostgreSQL DATABASE_URL before signing in.')
  }

  if (!response.ok) {
    let detail = response.status === 502 || response.status === 503
      ? 'BhoomiGuard API is unavailable. Start the FastAPI server and configure its PostgreSQL DATABASE_URL before signing in.'
      : `Request failed (HTTP ${response.status}).`
    try {
      const payload = await response.json()
      detail = errorMessage(payload.detail, detail)
    } catch {
      // Preserve the status-based message when the API has no JSON response.
    }
    if (response.status === 401) {
      sessionStorage.removeItem('bhoomiguard_access_token')
      sessionStorage.removeItem('bhoomiguard_user_name')
      window.dispatchEvent(new Event('bhoomiguard-auth-required'))
    }
    throw new Error(detail)
  }

  if (response.status === 204) return null
  return response
}

export async function getJson(path) {
  return (await apiRequest(path)).json()
}

export async function sendJson(path, method, body) {
  return (await apiRequest(path, { method, body: JSON.stringify(body) })).json()
}
