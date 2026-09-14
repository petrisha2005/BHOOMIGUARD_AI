import { useEffect, useState } from 'react'
import { navigate } from '../router'
import { getAuthenticationStatus, login } from '../services/bhoomiApi'

export function LoginPage({ accessMessage = '', authRequired: initialAuthRequired = null }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [fetchedAuthRequired, setFetchedAuthRequired] = useState(null)
  const authRequired = typeof initialAuthRequired === 'boolean'
    ? initialAuthRequired
    : fetchedAuthRequired

  useEffect(() => {
    if (typeof initialAuthRequired === 'boolean') return undefined
    let active = true
    getAuthenticationStatus()
      .then((status) => { if (active) setFetchedAuthRequired(Boolean(status?.auth_required)) })
      .catch(() => { if (active) setFetchedAuthRequired(true) })
    return () => { active = false }
  }, [initialAuthRequired])

  async function submit(event) {
    event.preventDefault()
    try {
      setSubmitting(true); setMessage('')
      const token = await login({ email, password })
      if (!token?.access_token) throw new Error('The server returned an invalid sign-in response.')
      sessionStorage.setItem('bhoomiguard_access_token', token.access_token)
      sessionStorage.setItem('bhoomiguard_user_name', token.name || '')
      navigate('/dashboard')
    } catch (error) { setMessage(error.message) } finally { setSubmitting(false) }
  }

  if (authRequired === false) return <main className="login-page"><section className="login-card"><div className="login-brand"><span>BG</span><div><h1>BhoomiGuard AI</h1><p>Land acquisition intelligence platform</p></div></div><h2>Local development workspace</h2><p className="page-description">Authentication is disabled by this server's local configuration. Production deployment must enable it after an authorized officer account is provisioned.</p><button className="primary-button" type="button" onClick={() => navigate('/dashboard')}>Continue to dashboard</button></section></main>

  return <main className="login-page"><section className="login-card"><div className="login-brand"><span>BG</span><div><h1>BhoomiGuard AI</h1><p>Land acquisition intelligence platform</p></div></div><h2>Officer sign in</h2><p className="page-description">Use an authorized officer account to access the BhoomiGuard workspace.</p>{accessMessage && <p className="form-error" role="status">{accessMessage}</p>}<form onSubmit={submit}><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" /></label>{message && <p className="form-error" role="alert">{message}</p>}<button className="primary-button" type="submit" disabled={submitting || authRequired === null}>{submitting ? 'Signing in…' : authRequired === null ? 'Checking access…' : 'Sign in'}</button></form></section></main>
}
