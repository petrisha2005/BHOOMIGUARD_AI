import { useCallback, useState } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { acknowledgeAlert, getAlerts, getProjects } from '../services/bhoomiApi'
import { formatDate } from '../utils/formatters'

export function AlertsPage() {
  const [acknowledged, setAcknowledged] = useState('')
  const [actionError, setActionError] = useState('')
  const loadAlerts = useCallback(() => Promise.all([
    getAlerts(acknowledged === '' ? '' : `?acknowledged=${acknowledged}`),
    getProjects(),
  ]), [acknowledged])
  const { data, error, loading, reload } = useApi(loadAlerts, [loadAlerts])
  const alerts = Array.isArray(data?.[0]) ? data[0] : []
  const projects = Array.isArray(data?.[1]) ? data[1] : []
  const projectById = Object.fromEntries(projects.map((project) => [project.id, project]))

  async function acknowledge(id) {
    try { setActionError(''); await acknowledgeAlert(id); await reload() }
    catch (requestError) { setActionError(requestError.message) }
  }

  return <section className="page-content"><PageTitle title="Alert Center" description="Review persisted project alerts, their reason, and acknowledgement state." /><section className="panel alerts-panel"><div className="filter-row"><label className="filter-label"><span><Icon name="filter" size={14} />Acknowledgement state</span><select value={acknowledged} onChange={(event) => setAcknowledged(event.target.value)}><option value="">All alerts</option><option value="false">Open alerts</option><option value="true">Acknowledged alerts</option></select></label></div>{actionError && <div className="notice error" role="alert"><Icon name="warning" />{actionError}</div>}<PageState loading={loading} error={error} empty={!loading && !error && alerts.length === 0} emptyIcon="alerts" emptyTitle="No alerts match this view."><div className="table-wrap"><table className="alerts-table"><caption className="sr-only">Project alerts</caption><thead><tr><th>Severity</th><th>Project</th><th>Alert type</th><th>Message / reason</th><th>Created</th><th>Status</th><th>Action</th></tr></thead><tbody>{alerts.map((alert) => { const project = projectById[alert.project_id]; return <tr key={alert.id}><td><Badge type="severity" value={alert.severity} /></td><td>{project ? <button className="table-link" type="button" onClick={() => navigate(`/projects/${project.id}`)}>{project.name}<small>{project.project_code}</small></button> : 'Project not available'}</td><td>{alert.alert_type || 'Not specified'}</td><td>{alert.message}</td><td>{formatDate(alert.created_at)}</td><td><Badge value={alert.acknowledged ? 'Acknowledged' : 'Open'} /></td><td>{!alert.acknowledged ? <button className="secondary-button compact-button" type="button" onClick={() => acknowledge(alert.id)}><Icon name="check" size={15} />Acknowledge</button> : <span className="muted-inline">No action needed</span>}</td></tr> })}</tbody></table></div></PageState></section></section>
}
