import { useCallback, useState } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { getProjectDetail, refreshProjectAssessment } from '../services/bhoomiApi'
import { displayValue, formatCompletionPercent, formatDate, formatRate } from '../utils/formatters'

function Metric({ label, value }) { return <div className="metric"><span>{label}</span><b>{value}</b></div> }
function RecordList({ title, icon, empty, records, render }) { const items = Array.isArray(records) ? records : []; return <section className="panel record-panel"><div className="panel-heading"><div><p className="section-kicker">Project record</p><h2>{title}</h2></div><Icon name={icon} size={19} /></div>{items.length === 0 ? <div className="inline-empty">{empty}</div> : <div className="record-list">{items.map((record) => <div className="record-item" key={record.id}>{render(record)}</div>)}</div>}</section> }

function bottleneckFor(project) {
  if ((project.legal_disputes || 0) > 0) return 'Legal disputes require review.'
  if ((project.ownership_conflicts || 0) > 0) return 'Ownership conflicts require resolution.'
  if ((project.pending_court_cases || 0) > 0) return 'Pending court cases require legal follow-up.'
  if ((project.pending_approvals || 0) > 0) return 'Pending approvals require coordination.'
  if ((project.missing_documents || 0) > 0) return 'Missing documents require completion.'
  return null
}

export function ProjectDetailPage({ projectId }) {
  const [refreshing, setRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState('')
  const [flash] = useState(() => {
    const message = sessionStorage.getItem('bhoomiguard_flash') || ''
    sessionStorage.removeItem('bhoomiguard_flash')
    return message
  })
  const loadDetail = useCallback(() => getProjectDetail(projectId), [projectId])
  const { data, error, loading } = useApi(loadDetail, [loadDetail])
  const project = data?.project && typeof data.project === 'object' && !Array.isArray(data.project) ? data.project : null
  const prediction = data?.latest_prediction && typeof data.latest_prediction === 'object' && !Array.isArray(data.latest_prediction) ? data.latest_prediction : null
  const technicalFactors = Array.isArray(prediction?.risk_factors) ? prediction.risk_factors : []
  const recommendations = Array.isArray(data?.recommendations) ? data.recommendations : []
  const alerts = Array.isArray(data?.alerts) ? data.alerts : []
  const interventions = Array.isArray(data?.interventions) ? data.interventions : []
  const bottleneck = project ? bottleneckFor(project) : null
  const progress = project ? [
    ['Documentation', project.documentation_completion_pct], ['Compensation', project.compensation_completion_pct], ['Rehabilitation', project.rehabilitation_completion_pct], ['Resettlement', project.resettlement_completion_pct], ['Possession', project.possession_completion_pct],
  ] : []

  async function refreshAssessment() {
    try { setRefreshing(true); setRefreshError(''); await refreshProjectAssessment(projectId); window.location.reload() }
    catch (requestError) { setRefreshError(requestError.message) } finally { setRefreshing(false) }
  }

  return <section className="page-content"><PageTitle eyebrow="Project overview" title={project ? project.name : 'Project Detail'} description={project ? `${project.project_code} · ${displayValue(project.district, 'District not recorded')} · ${displayValue(project.state, 'State not recorded')}` : 'Loading project data…'} action={<div className="title-actions"><button className="secondary-button" type="button" onClick={() => navigate('/projects')}><Icon name="arrowLeft" size={16} />Projects</button>{project && <><button className="secondary-button" type="button" disabled={refreshing} onClick={refreshAssessment}>Run ML assessment</button><button className="primary-button" type="button" onClick={() => navigate(`/projects/${project.id}/edit`)}><Icon name="edit" size={16} />Edit project</button></>}</div>} />{refreshError && <div className="notice error" role="alert"><Icon name="warning" />{refreshError}</div>}{flash && <div className="notice success" role="status"><Icon name="check" />{flash}</div>}<PageState loading={loading} error={error} empty={!loading && !error && !project} emptyIcon="projects" emptyTitle="This project could not be found.">{project && <><div className="project-hero-grid"><section className="panel span-two project-overview-panel"><div className="panel-heading"><div><p className="section-kicker">Officer-maintained project record</p><h2>Project overview</h2><p>Identity, location, land impact, and acquisition stage from the officer-maintained record.</p></div><Badge value={project.status} /></div><div className="metric-grid"><Metric label="Project type" value={displayValue(project.project_type)} /><Metric label="Current stage" value={displayValue(project.current_stage)} /><Metric label="Village" value={displayValue(project.village)} /><Metric label="Land area" value={project.land_area_acres == null ? 'Not available' : `${project.land_area_acres} acres`} /><Metric label="Affected families" value={displayValue(project.affected_families)} /><Metric label="Villages affected" value={displayValue(project.villages_affected)} /><Metric label="Days in stage" value={displayValue(project.days_in_current_stage)} /><Metric label="Days to target" value={displayValue(project.days_remaining_to_target)} /><Metric label="Historical delay rate" value={formatRate(project.historical_delay_rate)} /></div></section><section className="panel risk-panel"><div className="panel-heading"><div><p className="section-kicker">Decision support</p><h2>Risk</h2><p>Latest persisted prediction.</p></div>{prediction && <Badge type="risk" value={prediction.risk_category} />}</div><div className="metric-grid compact"><Metric label="Risk score" value={displayValue(prediction?.risk_score)} /><Metric label="Delay probability" value={formatRate(prediction?.delay_probability)} /><Metric label="Predicted delay" value={prediction?.predicted_delay_days == null ? 'Not available' : `${prediction.predicted_delay_days} days`} /><Metric label="Model version" value={displayValue(prediction?.model_version)} /></div></section></div><section className="panel acquisition-progress-panel"><div className="panel-heading"><div><p className="section-kicker">Officer-entered acquisition data</p><h2>Acquisition progress &amp; timeline</h2></div><Icon name="analytics" size={20} /></div><div className="progress-list">{progress.map(([label, value]) => <div className="progress-row" key={label}><span>{label}</span><div><i style={{ width: `${Math.min(100, Number(value || 0))}%` }} /></div><b>{formatCompletionPercent(value)}</b></div>)}</div></section><div className="detail-grid project-insight-grid"><section className="panel officer-factors-panel"><div className="panel-heading"><div><p className="section-kicker">Decision support explanation</p><h2>Why this project is at risk</h2><p>Factors shown are officer-facing ML SHAP aggregations.</p></div><Icon name="recommendations" size={19} /></div>{technicalFactors.length ? <div className="record-list">{technicalFactors.map((factor) => <div className="record-item" key={factor.id}><b>{factor.factor_name}</b><span>SHAP impact: {displayValue(factor.impact)} · {displayValue(factor.direction)}</span></div>)}</div> : <div className="inline-empty">Run an ML assessment once all canonical ML fields are supplied.</div>}</section><section className="panel bottleneck-panel"><div className="panel-heading"><div><p className="section-kicker">Operational focus</p><h2>Current bottleneck</h2></div><Icon name="warning" size={19} /></div>{bottleneck ? <div className="bottleneck-content"><b>{bottleneck}</b></div> : <div className="inline-empty">No current bottleneck can be identified from the available project fields.</div>}</section></div><div className="detail-grid project-records-grid"><RecordList title="Recommendations" icon="recommendations" empty="No recommendations have been recorded." records={recommendations} render={(item) => <><b>{item.title}</b><span>{displayValue(item.description)}</span><Badge type="priority" value={item.priority} /><Badge value={item.status} /></>} /><RecordList title="Alerts" icon="alerts" empty="No alerts have been recorded." records={alerts} render={(item) => <><b>{displayValue(item.alert_type, 'Alert')}</b><span>{item.message} · {formatDate(item.created_at)}</span><Badge type="severity" value={item.severity} /><Badge value={item.acknowledged ? 'Acknowledged' : 'Open'} /></>} /><RecordList title="Interventions" icon="interventions" empty="No interventions have been recorded." records={interventions} render={(item) => <><b>{item.action}</b><span>{displayValue(item.owner_role, 'Owner not recorded')} · Due {formatDate(item.due_date)}</span><Badge value={item.status} /></>} /></div></>}</PageState></section>
}
