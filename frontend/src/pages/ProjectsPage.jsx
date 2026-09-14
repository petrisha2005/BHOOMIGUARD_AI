import { useCallback, useMemo, useState } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { getProjects } from '../services/bhoomiApi'
import { displayValue, formatCompletionPercent } from '../utils/formatters'

export function ProjectsPage() {
  const loadProjects = useCallback(() => getProjects(), [])
  const { data, error, loading } = useApi(loadProjects, [loadProjects])
  const [search, setSearch] = useState('')
  const projects = useMemo(() => Array.isArray(data) ? data : [], [data])
  const visibleProjects = useMemo(() => {
    const query = search.trim().toLocaleLowerCase()
    if (!query) return projects
    return projects.filter((project) => [project.name, project.project_code, project.district, project.current_stage, project.status].some((value) => String(value ?? '').toLocaleLowerCase().includes(query)))
  }, [projects, search])

  return <section className="page-content"><PageTitle title="Projects" description="Live project portfolio and officer-managed canonical input data." action={<div className="title-actions"><button className="secondary-button" type="button" onClick={() => navigate('/projects/import')}><Icon name="upload" size={16} />Import CSV</button><button className="primary-button" type="button" onClick={() => navigate('/projects/new')}><Icon name="plus" size={16} />New project</button></div>} /><section className="panel projects-panel"><div className="portfolio-toolbar"><div><p className="toolbar-label"><Icon name="layers" size={15} />Portfolio register</p><span>{projects.length} live {projects.length === 1 ? 'project' : 'projects'}</span></div><label className="search-control"><span className="sr-only">Find a project</span><Icon name="search" size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find by project, district, stage or status" aria-label="Find a project" />{search && <button className="clear-search" type="button" onClick={() => setSearch('')} aria-label="Clear project search">Clear</button>}</label></div><PageState loading={loading} error={error} empty={!loading && !error && projects.length === 0} emptyIcon="projects" emptyTitle="No projects are available yet." emptyDescription="Create a project or import a validated CSV to begin monitoring the live portfolio.">{projects.length > 0 && visibleProjects.length === 0 ? <div className="state-panel search-empty"><Icon name="search" size={25} /><b>No projects match this search.</b><p>Try a project code, district, current stage, or status.</p><button className="secondary-button" type="button" onClick={() => setSearch('')}>Clear search</button></div> : <div className="table-wrap"><table className="projects-table"><caption className="sr-only">Live project portfolio</caption><thead><tr><th>Project</th><th>District</th><th>Stage</th><th>Documentation</th><th>Compensation</th><th>Status</th><th>Actions</th></tr></thead><tbody>{visibleProjects.map((project) => <tr key={project.id}><td><b>{project.name}</b><small>{project.project_code}</small></td><td>{displayValue(project.district, '—')}</td><td>{displayValue(project.current_stage, '—')}</td><td>{formatCompletionPercent(project.documentation_completion_pct)}</td><td>{formatCompletionPercent(project.compensation_completion_pct)}</td><td><Badge value={project.status} /></td><td><div className="row-actions"><button className="text-button" type="button" onClick={() => navigate(`/projects/${project.id}`)}><Icon name="eye" size={15} />Open</button><button className="text-button" type="button" onClick={() => navigate(`/projects/${project.id}/edit`)}><Icon name="edit" size={15} />Edit</button></div></td></tr>)}</tbody></table></div>}</PageState></section></section>
}
