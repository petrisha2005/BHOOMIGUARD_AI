import { useCallback, useState } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { createCase, getCases, getProjects } from '../services/bhoomiApi'
import { displayValue } from '../utils/formatters'

export function CasesPage() {
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [formMessage, setFormMessage] = useState('')
  const loadCases = useCallback(() => getCases(search ? `?search=${encodeURIComponent(search)}` : ''), [search])
  const casesState = useApi(loadCases, [loadCases])
  const loadProjects = useCallback(() => getProjects(), [])
  const projectsState = useApi(loadProjects, [loadProjects])
  const cases = Array.isArray(casesState.data) ? casesState.data : []
  const projects = Array.isArray(projectsState.data) ? projectsState.data : []

  async function submit(event) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    try { await createCase(Object.fromEntries([...form.entries()].filter(([, value]) => value !== ''))); setFormMessage('Case saved to the live database.'); event.currentTarget.reset(); casesState.reload() } catch (error) { setFormMessage(error.message) }
  }

  return <section className="page-content"><PageTitle title="Acquisition Cases" description="Search, review, create, and update land-acquisition cases from live records." action={<button className="primary-button" type="button" onClick={() => setShowForm(!showForm)}>{showForm ? 'Close form' : <><Icon name="plus" size={16} />New case</>}</button>} />
    {showForm && <section className="panel form-panel"><h2>Create acquisition case</h2><form className="data-form" onSubmit={submit}><label>Project<select name="project_id" required defaultValue=""><option value="" disabled>Select a project</option>{projects.map((project) => <option key={project.id} value={project.id}>{project.project_code} — {project.name}</option>)}</select></label><label>Case number<input name="case_number" required maxLength="100" /></label><label>Village<input name="village" maxLength="255" /></label><label>Current stage<input name="current_stage" maxLength="100" /></label><label>Case status<input name="case_status" maxLength="50" /></label><label>Days pending<input name="days_pending" type="number" min="0" /></label><button className="primary-button" type="submit">Save case</button></form>{formMessage && <p className="form-message">{formMessage}</p>}</section>}
    <section className="panel cases-panel"><div className="filter-row"><label className="search-control"><span className="sr-only">Search cases</span><Icon name="search" size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search case number or village" aria-label="Search cases" /></label><button className="secondary-button" type="button" onClick={casesState.reload}><Icon name="search" size={15} />Search</button></div><PageState loading={casesState.loading} error={casesState.error} empty={!casesState.loading && !casesState.error && cases.length === 0} emptyIcon="cases" emptyTitle="No acquisition cases are available yet."><div className="table-wrap"><table className="cases-table"><caption className="sr-only">Acquisition cases</caption><thead><tr><th>Case number</th><th>Village</th><th>Stage</th><th>Status</th><th>Days pending</th><th /></tr></thead><tbody>{cases.map((item) => <tr key={item.id}><td><b>{item.case_number}</b></td><td>{displayValue(item.village, '—')}</td><td>{displayValue(item.current_stage, '—')}</td><td><Badge value={item.case_status} /></td><td>{displayValue(item.days_pending, '—')}</td><td><button className="text-button" type="button" onClick={() => navigate(`/cases/${item.id}`)}><Icon name="eye" size={15} />Open</button></td></tr>)}</tbody></table></div></PageState></section></section>
}
