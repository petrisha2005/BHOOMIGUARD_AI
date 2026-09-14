import { useCallback, useState } from 'react'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { downloadProjectReport, getProjects } from '../services/bhoomiApi'

export function ReportsPage() {
  const loadProjects = useCallback(() => getProjects(), [])
  const { data, error, loading } = useApi(loadProjects, [loadProjects])
  const projects = Array.isArray(data) ? data : []
  const [message, setMessage] = useState('')
  async function download(project) { try { setMessage('Preparing report…'); const file = await downloadProjectReport(project.id); const url = URL.createObjectURL(file); const link = document.createElement('a'); link.href = url; link.download = `bhoomiguard-${project.project_code}.pdf`; link.click(); URL.revokeObjectURL(url); setMessage('Report downloaded.') } catch (requestError) { setMessage(requestError.message) } }
  return <section className="page-content"><PageTitle title="Reports" description="Generate a professional PDF using only persisted project, prediction, recommendation, alert, and intervention records." /><section className="panel reports-panel"><div className="panel-heading"><div><p className="section-kicker">Official project record</p><h2>Project reports</h2><p>Each report is generated from the selected project’s persisted records at download time.</p></div><Icon name="reports" size={20} /></div><PageState loading={loading} error={error} empty={!loading && !error && projects.length === 0} emptyIcon="reports" emptyTitle="No reports can be generated yet."><div className="report-list">{projects.map((project) => <div key={project.id}><div><b>{project.name}</b><small>{project.project_code}</small></div><button className="primary-button" type="button" onClick={() => download(project)}><Icon name="reports" size={16} />Download PDF</button></div>)}</div>{message && <p className="form-message" role="status">{message}</p>}</PageState></section></section>
}
