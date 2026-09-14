import { useCallback } from 'react'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { StatCard } from '../components/StatCard'
import { useApi } from '../hooks/useApi'
import { getAnalyticsOverview } from '../services/bhoomiApi'

function DistributionChart({ title, data, icon = 'analytics' }) {
  const items = Array.isArray(data) ? data : []
  const maximum = Math.max(...items.map((item) => item.value), 1)

  return <section className="panel chart-panel"><div className="chart-heading"><h2>{title}</h2><Icon name={icon} size={18} /></div>{items.length === 0 ? <div className="inline-empty">No persisted data is available for this chart.</div> : <div className="bar-list">{items.map((item) => <div key={item.label}><span>{item.label}</span><i><b style={{ width: `${(item.value / maximum) * 100}%` }} /></i><strong>{item.value}</strong></div>)}</div>}</section>
}

export function AnalyticsPage() {
  const loadAnalytics = useCallback(() => getAnalyticsOverview(), [])
  const { data, error, loading } = useApi(loadAnalytics, [loadAnalytics])
  const analytics = data && typeof data === 'object' && !Array.isArray(data) ? data : null
  const projectCreationTrend = Array.isArray(analytics?.project_creation_trend)
    ? analytics.project_creation_trend.map((item) => ({ label: item.period, value: item.value }))
    : []

  return <section className="page-content"><PageTitle title="Analytics" description="Live portfolio distributions and creation trend derived from persisted project records." /><PageState loading={loading} error={error} empty={!loading && !error && !analytics} emptyIcon="analytics" emptyTitle="Analytics are not available yet.">{analytics && <><div className="stats-grid"><StatCard label="Total Projects" value={analytics.total_projects} icon={<Icon name="projects" size={19} />} /><StatCard label="Active Projects" value={analytics.active_projects} tone="green" icon={<Icon name="check" size={19} />} /><StatCard label="High / Critical Risk" value={analytics.high_critical_risk_projects} tone="orange" icon={<Icon name="warning" size={19} />} /><StatCard label="Delayed Projects" value={analytics.delayed_projects} tone="red" icon={<Icon name="clock" size={19} />} /></div><div className="detail-grid analytics-grid"><DistributionChart title="Projects by District" data={analytics.projects_by_district} icon="location" /><DistributionChart title="Risk Distribution" data={analytics.risk_distribution} icon="warning" /><DistributionChart title="Project Status" data={analytics.status_distribution} icon="dashboard" /><DistributionChart title="Acquisition Stages" data={analytics.stage_distribution} icon="cases" /><DistributionChart title="Project Creation Trend" data={projectCreationTrend} icon="analytics" /></div></>}</PageState></section>
}
