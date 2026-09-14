import { useCallback, useState } from 'react'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { getProjects, runProjectWhatIf } from '../services/bhoomiApi'

export function WhatIfPage() {
  const [projectId, setProjectId] = useState('')
  const [scenario, setScenario] = useState({ documentation_completion_pct: '', compensation_completion_pct: '', pending_approvals: '' })
  const [result, setResult] = useState(null)
  const [actionError, setActionError] = useState('')
  const [running, setRunning] = useState(false)
  const loadProjects = useCallback(() => getProjects(), [])
  const { data, error, loading } = useApi(loadProjects, [loadProjects])
  const projects = Array.isArray(data) ? data : []

  async function submit(event) {
    event.preventDefault()
    const changes = Object.fromEntries(Object.entries(scenario).filter(([, value]) => value !== '').map(([key, value]) => [key, Number(value)]))
    if (!projectId) { setActionError('Choose a project.'); return }
    if (!Object.keys(changes).length) { setActionError('Enter at least one scenario change.'); return }
    try { setRunning(true); setActionError(''); setResult(await runProjectWhatIf(projectId, changes)) }
    catch (requestError) { setActionError(requestError.message) } finally { setRunning(false) }
  }

  return <section className="page-content"><PageTitle title="What-If Scenario" description="Run a non-persistent scenario through the same BhoomiGuard ML model used for project assessments." />{actionError && <div className="notice error" role="alert"><Icon name="warning" />{actionError}</div>}<PageState loading={loading} error={error} empty={!loading && !error && projects.length === 0} emptyIcon="projects" emptyTitle="Create a complete project before running a scenario."><section className="whatif-grid"><form className="panel scenario-card" onSubmit={submit}><div className="panel-heading"><div><h2>Scenario inputs</h2><p>Only changed canonical ML fields are sent. Results are not stored as a project assessment.</p></div><Icon name="whatif" size={21} /></div><div className="scenario-fields"><label>Project<select value={projectId} onChange={(event) => setProjectId(event.target.value)} required><option value="">Choose project</option>{projects.map((project) => <option value={project.id} key={project.id}>{project.name} ({project.project_code})</option>)}</select></label><label>Documentation Completion (%)<input type="number" min="0" max="100" value={scenario.documentation_completion_pct} onChange={(event) => setScenario({ ...scenario, documentation_completion_pct: event.target.value })} /></label><label>Compensation Completion (%)<input type="number" min="0" max="100" value={scenario.compensation_completion_pct} onChange={(event) => setScenario({ ...scenario, compensation_completion_pct: event.target.value })} /></label><label>Pending Approvals<input type="number" min="0" step="1" value={scenario.pending_approvals} onChange={(event) => setScenario({ ...scenario, pending_approvals: event.target.value })} /></label></div><button className="primary-button" type="submit" disabled={running}><Icon name="whatif" size={16} />{running ? 'Running scenario…' : 'Run scenario'}</button></form><article className="panel scenario-card dependency-card"><Icon name="whatif" size={30} /><h2>Model projection</h2>{result ? <><div className="baseline-comparison"><div><span>Baseline</span><b>{result.baseline.risk_score}% · {result.baseline.risk_category}</b></div><div><span>Scenario</span><b>{result.scenario.risk_score}% · {result.scenario.risk_category}</b></div><div><span>Risk change</span><b>{result.impact.risk_score_change_percentage_points} points</b></div></div><p>{result.interpretation}</p><small>{result.duration_note}</small></> : <p>Choose a project and enter changes to compare the baseline and scenario risk. The ML support-range validation remains active.</p>}</article></section></PageState></section>
}
