import { useCallback, useState } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { createIntervention, getInterventions, getProjects, updateIntervention } from '../services/bhoomiApi'
import { displayValue, formatDate } from '../utils/formatters'

function InterventionFields({ projects, initial, onSubmit, submitting, create }) {
  return <form className="data-form intervention-form" onSubmit={onSubmit}><label>Project{create ? <select name="project_id" required defaultValue=""><option value="" disabled>Select a project</option>{projects.map((project) => <option value={project.id} key={project.id}>{project.project_code} — {project.name}</option>)}</select> : <input value={initial.project_name || 'Project record'} disabled />}</label><label>Officer action<textarea name="action" required defaultValue={initial?.action || ''} /></label><label>Intervention type<input name="intervention_type" defaultValue={initial?.intervention_type || ''} placeholder="e.g. Document review" /></label><label>Owner / responsible role<input name="owner_role" defaultValue={initial?.owner_role || ''} /></label><label>Status<select name="status" defaultValue={initial?.status || 'Pending'}><option>Pending</option><option>In Progress</option><option>Completed</option><option>Deferred</option></select></label><label>Due date<input name="due_date" type="date" defaultValue={initial?.due_date || ''} /></label><label className="span-three">Resolution notes<textarea name="notes" defaultValue={initial?.notes || ''} /></label><button className="primary-button" type="submit" disabled={submitting}><Icon name="check" size={16} />{submitting ? 'Saving…' : create ? 'Create intervention' : 'Save intervention'}</button></form>
}

export function InterventionsPage() {
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [message, setMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const loadInterventions = useCallback(() => getInterventions(), [])
  const interventionState = useApi(loadInterventions, [loadInterventions])
  const loadProjects = useCallback(() => getProjects(), [])
  const projectsState = useApi(loadProjects, [loadProjects])
  const interventions = Array.isArray(interventionState.data) ? interventionState.data : []
  const projects = Array.isArray(projectsState.data) ? projectsState.data : []
  const projectById = Object.fromEntries(projects.map((project) => [project.id, project]))

  async function create(event) {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    try { setSubmitting(true); setActionError(''); await createIntervention(Object.fromEntries([...form.entries()].filter(([, value]) => value !== ''))); setMessage('Intervention saved to the live database.'); setShowForm(false); await interventionState.reload() } catch (requestError) { setActionError(requestError.message) } finally { setSubmitting(false) }
  }
  async function saveEdit(event) {
    event.preventDefault(); const form = new FormData(event.currentTarget)
    try { setSubmitting(true); setActionError(''); await updateIntervention(editing.id, Object.fromEntries([...form.entries()].filter(([key, value]) => key !== 'project_id' && value !== ''))); setMessage('Intervention updated.'); setEditing(null); await interventionState.reload() } catch (requestError) { setActionError(requestError.message) } finally { setSubmitting(false) }
  }
  const editingWithProject = editing && { ...editing, project_name: projectById[editing.project_id]?.name }

  return <section className="page-content"><PageTitle title="Interventions" description="Operational follow-through from a recommendation or alert to officer action, owner, due date, and resolution." action={<button className="primary-button" type="button" onClick={() => { setShowForm(!showForm); setEditing(null) }}><Icon name="plus" size={16} />{showForm ? 'Close form' : 'New intervention'}</button>} />{actionError && <div className="notice error" role="alert"><Icon name="warning" />{actionError}</div>}{message && <div className="notice success" role="status"><Icon name="check" />{message}</div>}{showForm && <section className="panel form-panel"><h2>Create intervention</h2><InterventionFields projects={projects} initial={{}} onSubmit={create} submitting={submitting} create /></section>}{editingWithProject && <section className="panel form-panel"><div className="panel-heading"><h2>Edit intervention</h2><button className="text-button" type="button" onClick={() => setEditing(null)}>Cancel</button></div><InterventionFields projects={projects} initial={editingWithProject} onSubmit={saveEdit} submitting={submitting} /></section>}<section className="panel interventions-panel"><PageState loading={interventionState.loading} error={interventionState.error} empty={!interventionState.loading && !interventionState.error && interventions.length === 0} emptyIcon="interventions" emptyTitle="No interventions are available yet."><div className="table-wrap"><table className="interventions-table"><caption className="sr-only">Project interventions</caption><thead><tr><th>Officer action</th><th>Project</th><th>Owner</th><th>Due date</th><th>Status</th><th>Resolution</th><th /></tr></thead><tbody>{interventions.map((item) => <tr key={item.id}><td><b>{item.action}</b><small>{displayValue(item.intervention_type, 'Intervention')}</small></td><td>{projectById[item.project_id]?.name || 'Project record'}</td><td>{displayValue(item.owner_role, 'Not assigned')}</td><td>{formatDate(item.due_date)}</td><td><Badge value={item.status} /></td><td>{displayValue(item.notes, '—')}</td><td><button className="text-button" type="button" onClick={() => { setEditing(item); setShowForm(false) }}><Icon name="edit" size={15} />Edit</button></td></tr>)}</tbody></table></div></PageState></section></section>
}
