import { useEffect, useState } from 'react'
import { AppLayout } from './layouts/AppLayout'
import { useRoute, navigate } from './router'
import { AlertsPage } from './pages/AlertsPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { CaseDetailPage } from './pages/CaseDetailPage'
import { CasesPage } from './pages/CasesPage'
import { DashboardPage } from './pages/DashboardPage'
import { InterventionsPage } from './pages/InterventionsPage'
import { LoginPage } from './pages/LoginPage'
import { MapPage } from './pages/MapPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ProjectCreatePage, ProjectEditPage } from './pages/ProjectEditorPages'
import { ProjectImportPage } from './pages/ProjectImportPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { RecommendationsPage } from './pages/RecommendationsPage'
import { ReportsPage } from './pages/ReportsPage'
import { WhatIfPage } from './pages/WhatIfPage'
import { getAuthenticationStatus } from './services/bhoomiApi'
import './App.css'

function NotFoundPage() { return <section className="page-content"><div className="state-panel"><b>Page not found.</b><p>The requested BhoomiGuard workspace route does not exist.</p><button className="primary-button" type="button" onClick={() => navigate('/dashboard')}>Open dashboard</button></div></section> }

function RoutedWorkspace({ path }) {
  if (path === '/dashboard' || path === '/') return <DashboardPage />
  if (path === '/projects/new') return <ProjectCreatePage />
  if (path === '/projects/import') return <ProjectImportPage />
  if (/^\/projects\/[^/]+\/edit$/.test(path)) return <ProjectEditPage projectId={path.split('/')[2]} />
  if (path === '/projects') return <ProjectsPage />
  if (/^\/projects\/[^/]+$/.test(path)) return <ProjectDetailPage projectId={path.split('/')[2]} />
  if (path === '/cases') return <CasesPage />
  if (/^\/cases\/[^/]+$/.test(path)) return <CaseDetailPage caseId={path.split('/')[2]} />
  if (path === '/alerts') return <AlertsPage />
  if (path === '/recommendations') return <RecommendationsPage />
  if (path === '/interventions') return <InterventionsPage />
  if (path === '/map') return <MapPage />
  if (path === '/analytics') return <AnalyticsPage />
  if (path === '/reports') return <ReportsPage />
  if (path === '/what-if') return <WhatIfPage />
  return <NotFoundPage />
}

function App() {
  const path = useRoute()
  const [authRequired, setAuthRequired] = useState(null)
  const [authStatusError, setAuthStatusError] = useState('')
  useEffect(() => {
    const requireLogin = () => navigate('/login')
    window.addEventListener('bhoomiguard-auth-required', requireLogin)
    return () => window.removeEventListener('bhoomiguard-auth-required', requireLogin)
  }, [])
  useEffect(() => {
    let active = true
    getAuthenticationStatus()
      .then((status) => { if (active) setAuthRequired(Boolean(status?.auth_required)) })
      .catch((error) => { if (active) setAuthStatusError(error.message || 'Unable to verify access configuration.') })
    return () => { active = false }
  }, [])
  if (path === '/login') return <LoginPage authRequired={authRequired} />
  if (authStatusError) return <LoginPage accessMessage={authStatusError} />
  if (authRequired === null) return <LoginPage accessMessage="Checking workspace access…" />
  if (authRequired && !sessionStorage.getItem('bhoomiguard_access_token')) return <LoginPage accessMessage="Sign in to access the officer workspace." />
  return <AppLayout><RoutedWorkspace path={path} /></AppLayout>
}

export default App
