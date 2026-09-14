import { useCallback } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { StatCard } from '../components/StatCard'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { getAnalyticsOverview, getAttentionProjects } from '../services/bhoomiApi'
import { displayValue, formatRate } from '../utils/formatters'

export function DashboardPage() {
  const loadDashboard = useCallback(() => Promise.all([getAnalyticsOverview(), getAttentionProjects()]), [])
  const { data, error, loading } = useApi(loadDashboard, [loadDashboard])
  const overview = data?.[0]
  const attention = Array.isArray(data?.[1]) ? data[1] : []
  const hasOverview = overview && typeof overview === 'object' && !Array.isArray(overview)
  const riskDistribution = Array.isArray(overview?.risk_distribution) ? overview.risk_distribution : []
  const maximumRiskCount = Math.max(...riskDistribution.map((item) => item.value), 1)

  return <section className="page-content">
    <PageTitle title="Land Acquisition Monitoring Dashboard" description="Monitor project readiness, operational bottlenecks, and records requiring officer attention." action={<span className="live-pill"><i />Live API data</span>} />
    <PageState loading={loading} error={error} empty={!loading && !error && !hasOverview}>
      {hasOverview && <>
        <div className="stats-grid dashboard-stats"><StatCard label="Total Projects" value={overview.total_projects} icon={<Icon name="projects" size={19} />} /><StatCard label="Active Projects" value={overview.active_projects} tone="green" icon={<Icon name="dashboard" size={19} />} /><StatCard label="High / Critical Risk" value={overview.high_critical_risk_projects} tone="orange" caption="Latest persisted predictions" icon={<Icon name="warning" size={19} />} /><StatCard label="Open Alerts" value={overview.open_alerts} tone="red" icon={<Icon name="alerts" size={19} />} /><StatCard label="Active Cases" value={overview.active_cases} tone="blue" icon={<Icon name="cases" size={19} />} /><StatCard label="Delayed Projects" value={overview.delayed_projects} tone="red" icon={<Icon name="clock" size={19} />} /></div>
        <div className="dashboard-detail-grid"><section className="panel risk-distribution-panel"><div className="panel-heading"><div><h2>Risk Distribution</h2><p>Latest persisted risk categories only.</p></div><Icon name="analytics" size={20} /></div>{riskDistribution.length === 0 ? <div className="inline-empty">No persisted prediction categories are available yet.</div> : <div className="bar-list">{riskDistribution.map((item) => <div key={item.label}><span>{item.label}</span><i><b style={{ width: `${(item.value / maximumRiskCount) * 100}%` }} /></i><strong>{item.value}</strong></div>)}</div>}</section><section className="panel dashboard-context"><div className="panel-heading"><div><h2>Decision Support Status</h2><p>Current data coverage from the live platform.</p></div><Icon name="check" size={20} /></div><div className="context-list"><div><span>Operational monitoring</span><b>Live Supabase data</b></div><div><span>Prediction refresh</span><b>Role 1 service required</b></div><div><span>Delay trend</span><b>Not available from current records</b></div></div></section></div>
        <section className="panel attention-panel"><div className="panel-heading"><div><p className="section-kicker">Officer review queue</p><h2>Projects Requiring Attention</h2><p>Persisted risk signals, delay conditions, and operational bottlenecks requiring officer review.</p></div><span className="count-chip">{attention.length} projects</span></div>
          <PageState empty={attention.length === 0} emptyIcon="warning" emptyTitle="No projects currently require attention." emptyDescription="This queue will show persisted risk signals and operational bottlenecks when they are available."><div className="table-wrap"><table className="attention-table"><caption className="sr-only">Projects requiring officer attention</caption><thead><tr><th>Project</th><th>District</th><th>Current stage</th><th>Risk</th><th>Delay probability</th><th>Expected delay</th><th>Bottleneck</th><th>Action</th></tr></thead><tbody>{attention.map((project) => <tr key={project.id}><td><b>{project.name}</b><small>{project.project_code}</small></td><td>{displayValue(project.district, '—')}</td><td>{displayValue(project.current_stage, '—')}</td><td><Badge type="risk" value={project.risk_category} /></td><td>{formatRate(project.delay_probability)}</td><td>{project.predicted_delay_days == null ? 'Not available' : `${project.predicted_delay_days} days`}</td><td>{displayValue(project.bottleneck, 'Not identified')}</td><td><button className="text-button" type="button" onClick={() => navigate(`/projects/${project.id}`)}><Icon name="eye" size={15} />Review</button></td></tr>)}</tbody></table></div></PageState>
        </section>
      </>}
    </PageState>
  </section>
}
