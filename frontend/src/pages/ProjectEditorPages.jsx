import { useCallback, useState } from 'react'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { ProjectForm } from '../components/ProjectForm'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { createProject, getProject, updateProject } from '../services/bhoomiApi'

export function ProjectCreatePage() {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  async function save(payload) {
    try {
      setSubmitting(true); setError(''); setMessage('')
      const project = await createProject(payload)
      sessionStorage.setItem('bhoomiguard_flash', 'Project saved to the BhoomiGuard database.')
      navigate(`/projects/${project.id}`)
    } catch (requestError) { setError(requestError.message) } finally { setSubmitting(false) }
  }
  return <section className="page-content"><PageTitle title="Create Project" description="Record project information and operational inputs without generating a prediction." action={<button className="secondary-button" type="button" onClick={() => navigate('/projects')}><Icon name="arrowLeft" size={16} />Projects</button>} />{error && <div className="notice error"><Icon name="warning" />{error}</div>}{message && <div className="notice success"><Icon name="check" />{message}</div>}<ProjectForm onSave={save} submitting={submitting} submitLabel="Save project" /></section>
}

export function ProjectEditPage({ projectId }) {
  const loadProject = useCallback(() => getProject(projectId), [projectId])
  const { data, error: loadError, loading } = useApi(loadProject, [loadProject])
  const project = data && typeof data === 'object' ? data : null
  const [message, setMessage] = useState('')
  const [saveError, setSaveError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  async function save(payload) {
    try {
      setSubmitting(true); setSaveError(''); setMessage('')
      await updateProject(projectId, payload)
      setMessage('Project changes saved to the BhoomiGuard database.')
    } catch (requestError) { setSaveError(requestError.message) } finally { setSubmitting(false) }
  }
  return <section className="page-content"><PageTitle title={project ? `Edit ${project.project_code}` : 'Edit Project'} description="Update the officer-maintained project record and canonical input fields." action={<button className="secondary-button" type="button" onClick={() => navigate(`/projects/${projectId}`)}><Icon name="arrowLeft" size={16} />Project detail</button>} /><PageState loading={loading} error={loadError} empty={!loading && !loadError && !project}>{project && <>{saveError && <div className="notice error"><Icon name="warning" />{saveError}</div>}{message && <div className="notice success"><Icon name="check" />{message}</div>}<ProjectForm key={project.id} initialProject={project} onSave={save} submitting={submitting} submitLabel="Save changes" /></>}</PageState></section>
}
