import { useCallback, useState } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { getProjects, getRecommendations, updateRecommendation } from '../services/bhoomiApi'
import { displayValue } from '../utils/formatters'

export function RecommendationsPage() {
  const loadData = useCallback(() => Promise.all([getRecommendations(), getProjects()]), [])
  const { data, error, loading, reload } = useApi(loadData, [loadData])
  const [actionError, setActionError] = useState('')
  const [savingId, setSavingId] = useState('')
  const recommendations = Array.isArray(data?.[0]) ? data[0] : []
  const projects = Array.isArray(data?.[1]) ? data[1] : []
  const projectById = Object.fromEntries(projects.map((project) => [project.id, project]))

  async function updateStatus(item, status) {
    try { setSavingId(item.id); setActionError(''); await updateRecommendation(item.id, { status }); await reload() }
    catch (requestError) { setActionError(requestError.message) } finally { setSavingId('') }
  }

  return <section className="page-content"><PageTitle title="Recommendations" description="Officer actions recorded against live project records. Recommendation intelligence remains owned by Role 1." />{actionError && <div className="notice error" role="alert"><Icon name="warning" />{actionError}</div>}<section className="card-grid recommendation-grid"><PageState loading={loading} error={error} empty={!loading && !error && recommendations.length === 0} emptyIcon="recommendations" emptyTitle="No recommendations are available yet.">{recommendations.map((item) => { const project = projectById[item.project_id]; return <article className="action-card recommendation-card" key={item.id}><div className="card-status-row"><Badge type="priority" value={item.priority} /><Badge value={item.status} /></div><h2>{item.title}</h2><div className="recommendation-fields"><div><span>Project</span><b>{project?.name || 'Project record unavailable'}</b></div><div><span>Recommended action</span><p>{displayValue(item.description, 'No action description recorded.')}</p></div><div><span>Responsible role</span><b>Not recorded</b></div><div><span>Monitoring information</span><b>Not recorded</b></div></div><div className="card-footer"><button className="text-button" type="button" onClick={() => navigate(`/projects/${item.project_id}`)}><Icon name="eye" size={15} />Open project</button><label>Update status<select value={item.status || 'Pending'} disabled={savingId === item.id} onChange={(event) => updateStatus(item, event.target.value)}><option>Pending</option><option>In Progress</option><option>Completed</option><option>Deferred</option></select></label></div></article> })}</PageState></section></section>
}
