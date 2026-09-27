import { useCallback, useEffect, useState } from 'react'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { ProjectMap } from '../components/ProjectMap'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { createIntervention, getAlerts, getCase, getInterventions, getMapParcel, getMapParcels, getMapProjects, getRecommendations } from '../services/bhoomiApi'
import { displayValue, formatDate } from '../utils/formatters'

function formatOwnership(value) { return value === 'GOVERNMENT' ? 'Government' : 'Private' }
function formatStatus(value) { return String(value || '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase()) || 'Not recorded' }
function formatProbability(value) { return value == null ? 'Not available' : `${(Number(value) * 100).toFixed(1)}%` }

function ProjectRecords({ title, empty, records, render }) {
  return <section className="parcel-record-section"><h3>{title}</h3>{records.length ? <div className="parcel-record-list">{records.map((record) => <div key={record.id}>{render(record)}</div>)}</div> : <p>{empty}</p>}</section>
}

export function MapPage() {
  const [mapError, setMapError] = useState('')
  const [selectedProject, setSelectedProject] = useState(null)
  const [parcels, setParcels] = useState([])
  const [parcelsLoading, setParcelsLoading] = useState(false)
  const [parcelError, setParcelError] = useState('')
  const [selectedParcelId, setSelectedParcelId] = useState(null)
  const [selectedParcel, setSelectedParcel] = useState(null)
  const [workflow, setWorkflow] = useState({ caseItem: null, recommendations: [], alerts: [], interventions: [] })
  const [workflowLoading, setWorkflowLoading] = useState(false)
  const [workflowError, setWorkflowError] = useState('')
  const [showInterventionForm, setShowInterventionForm] = useState(false)
  const [interventionMessage, setInterventionMessage] = useState('')
  const [submittingIntervention, setSubmittingIntervention] = useState(false)
  const loadLocations = useCallback(() => getMapProjects(), [])
  const { data, error, loading } = useApi(loadLocations, [loadLocations])
  const projects = Array.isArray(data) ? data : []
  const clearSelection = useCallback(() => { setSelectedParcelId(null); setSelectedParcel(null); setWorkflow({ caseItem: null, recommendations: [], alerts: [], interventions: [] }); setWorkflowError(''); setShowInterventionForm(false); setInterventionMessage('') }, [])
  const selectProject = useCallback((project) => { setSelectedProject(project); setParcels([]); setParcelError(''); clearSelection() }, [clearSelection])
  const clearParcels = useCallback(() => { setSelectedProject(null); setParcels([]); setParcelError(''); clearSelection() }, [clearSelection])

  useEffect(() => {
    if (!selectedProject?.id) return undefined
    let active = true
    setParcelsLoading(true)
    getMapParcels(selectedProject.id)
      .then((result) => { if (active) setParcels(Array.isArray(result) ? result : []) })
      .catch((requestError) => { if (active) { setParcels([]); setParcelError(requestError.message || 'Unable to load project parcels.') } })
      .finally(() => { if (active) setParcelsLoading(false) })
    return () => { active = false }
  }, [selectedProject?.id])

  const selectParcel = useCallback((parcelId) => {
    const fallback = parcels.find((parcel) => parcel.id === parcelId) || null
    setSelectedParcelId(parcelId); setSelectedParcel(fallback); setWorkflowError(''); setInterventionMessage(''); setShowInterventionForm(false)
    getMapParcel(parcelId).then(setSelectedParcel).catch((requestError) => setWorkflowError(`Parcel detail could not be refreshed. ${requestError.message || ''}`))
  }, [parcels])

  useEffect(() => {
    if (!selectedParcel || !selectedProject?.id) return undefined
    let active = true
    setWorkflowLoading(true); setWorkflowError('')
    const caseRequest = selectedParcel.acquisition_case_id ? getCase(selectedParcel.acquisition_case_id) : Promise.resolve(null)
    Promise.allSettled([caseRequest, getRecommendations(`?project_id=${selectedProject.id}`), getAlerts(`?project_id=${selectedProject.id}`), getInterventions(`?project_id=${selectedProject.id}`)])
      .then(([caseResult, recommendationsResult, alertsResult, interventionsResult]) => {
        if (!active) return
        const failures = [caseResult, recommendationsResult, alertsResult, interventionsResult].filter((result) => result.status === 'rejected')
        setWorkflow({
          caseItem: caseResult.status === 'fulfilled' ? caseResult.value : null,
          recommendations: recommendationsResult.status === 'fulfilled' && Array.isArray(recommendationsResult.value) ? recommendationsResult.value : [],
          alerts: alertsResult.status === 'fulfilled' && Array.isArray(alertsResult.value) ? alertsResult.value : [],
          interventions: interventionsResult.status === 'fulfilled' && Array.isArray(interventionsResult.value) ? interventionsResult.value : [],
        })
        if (failures.length) setWorkflowError('Some project workflow records could not be loaded. Parcel details remain available.')
      })
      .finally(() => { if (active) setWorkflowLoading(false) })
    return () => { active = false }
  }, [selectedParcel, selectedProject?.id])

  async function recordIntervention(event) {
    event.preventDefault()
    if (!selectedProject || !selectedParcel) return
    const form = new FormData(event.currentTarget)
    const payload = Object.fromEntries([...form.entries()].filter(([, value]) => value !== ''))
    const caseReference = workflow.caseItem ? `; acquisition case ${workflow.caseItem.case_number}` : ''
    const officerNotes = payload.notes ? `${payload.notes}\n\n` : ''
    payload.project_id = selectedProject.id
    payload.notes = `${officerNotes}GIS follow-up: synthetic demo parcel ${selectedParcel.parcel_id}${caseReference}.`
    try {
      setSubmittingIntervention(true); setInterventionMessage('')
      const created = await createIntervention(payload)
      setWorkflow((current) => ({ ...current, interventions: [created, ...current.interventions] }))
      setInterventionMessage('Intervention saved as a project-level operational record.')
      setShowInterventionForm(false)
    } catch (requestError) { setInterventionMessage(requestError.message || 'Intervention could not be saved.') } finally { setSubmittingIntervention(false) }
  }

  return <section className="page-content">
    <PageTitle title="GIS Project Map" description="Project markers use persisted coordinates; corridors and parcel polygons are synthetic demonstration data." />
    <section className="panel map-panel">
      <div className="map-toolbar"><span><Icon name="location" size={16} />Live project locations</span><span>{selectedProject ? `${selectedProject.project_code}: ${parcels.length} demo parcels` : `${projects.length} mapped ${projects.length === 1 ? 'project' : 'projects'}`}</span></div>
      <div className="map-legend" aria-label="Project, corridor, and parcel map legend">
        <div><b>Project marker</b><span><i className="map-dot critical" />Critical</span><span><i className="map-dot high" />High</span><span><i className="map-dot medium" />Moderate</span></div>
        <div><b>GIS layers</b><span><i className="map-dot" />Project location</span><span><i className="corridor-swatch" />Infrastructure corridor</span></div>
        <div><b>Parcel ownership</b><span><i className="parcel-swatch government" />Government</span><span><i className="parcel-swatch private" />Private</span></div>
        <div><b>Parcel outline</b><span><i className="parcel-line acquired" />Acquired</span><span><i className="parcel-line disputed" />Disputed</span><span><i className="parcel-line on-hold" />On hold</span></div>
      </div>
      <PageState loading={loading} error={error || mapError} empty={!loading && !error && projects.length === 0} emptyIcon="map" emptyTitle="No mapped projects are available yet." emptyDescription="Project markers are shown only when persisted latitude and longitude are available.">
        <ProjectMap projects={projects} parcels={parcels} selectedProjectId={selectedProject?.id} selectedParcelId={selectedParcelId} onProjectSelect={selectProject} onParcelSelect={selectParcel} onError={setMapError} />
      </PageState>
    </section>
    {selectedProject && <section className="detail-grid parcel-workspace">
      <section className="panel parcel-context-panel">
        <div className="panel-heading"><div><p className="section-kicker">Project → corridor → parcels</p><h2>{selectedProject.project_code}</h2><p>{selectedProject.corridor_geometry ? 'A synthetic infrastructure corridor and development-only parcel polygons can be explored around the selected project marker.' : 'Development-only parcel polygons can be explored around the selected project marker.'}</p></div><button className="secondary-button" type="button" onClick={clearParcels}>Clear parcels</button></div>
        {selectedProject.corridor_geometry && <div className="corridor-summary"><span>Demo corridor data</span><span>This visualization is not a legal acquisition boundary or spatial-intersection analysis.</span></div>}
        {parcelsLoading && <p className="inline-loading">Loading demo parcels…</p>}
        {parcelError && <p className="parcel-error" role="alert">Parcel data could not be loaded. Project markers remain available. {parcelError}</p>}
        {!parcelsLoading && !parcelError && parcels.length === 0 && <p className="inline-empty">No synthetic demo parcels are available for this project.</p>}
        {parcels.length > 0 && <div className="parcel-summary"><span>Demo parcel data</span><span>Click a polygon to review its acquisition workflow and parent project context.</span></div>}
      </section>
      {selectedParcel ? <section className="panel parcel-detail-panel">
        <div className="panel-heading"><div><p className="section-kicker">Selected parcel · demo data</p><h2>{selectedParcel.parcel_id}</h2><p>Polygon, ownership, and area are synthetic development data.</p></div></div>
        <div className="metric-grid compact"><div className="metric"><span>Ownership</span><b>{formatOwnership(selectedParcel.ownership_type)}</b></div><div className="metric"><span>Area</span><b>{selectedParcel.area_acres} acres</b></div><div className="metric"><span>Acquisition status</span><b>{formatStatus(selectedParcel.acquisition_status)}</b></div><div className="metric"><span>Project risk context</span><b>{selectedParcel.latest_project_risk?.risk_category || 'Unassessed'}</b></div><div className="metric"><span>Project risk probability</span><b>{formatProbability(selectedParcel.latest_project_risk?.delay_probability)}</b></div></div>
        {workflowLoading && <p className="inline-loading">Loading linked case and project workflow records…</p>}
        {workflowError && <p className="parcel-error" role="alert">{workflowError}</p>}
        {!workflowLoading && <div className="parcel-workflow">
          <section className="parcel-record-section"><h3>Acquisition case</h3>{workflow.caseItem ? <><div className="parcel-case-grid"><span>Case ID<b>{workflow.caseItem.case_number}</b></span><span>Case status<b>{displayValue(workflow.caseItem.case_status)}</b></span><span>Current stage<b>{displayValue(workflow.caseItem.current_stage)}</b></span><span>Documentation<b>{displayValue(workflow.caseItem.documentation_status)}</b></span><span>Compensation<b>{displayValue(workflow.caseItem.compensation_status)}</b></span><span>Dispute<b>{displayValue(workflow.caseItem.dispute_status)}</b></span></div><button className="secondary-button" type="button" onClick={() => navigate(`/cases/${workflow.caseItem.id}`)}>Open Acquisition Case</button></> : <p>No acquisition case linked.</p>}</section>
          <ProjectRecords title="Project recommendations" empty="No recommendations currently recorded." records={workflow.recommendations} render={(item) => <><b>{item.title}</b><span>{displayValue(item.description)}</span><small>{displayValue(item.priority, 'Priority not recorded')} · {displayValue(item.status, 'Status not recorded')}</small></>} />
          <ProjectRecords title="Project alerts" empty="No active alerts." records={workflow.alerts} render={(item) => <><b>{displayValue(item.alert_type, 'Alert')}</b><span>{item.message}</span><small>{displayValue(item.severity, 'Severity not recorded')} · {item.acknowledged ? 'Acknowledged' : 'Open'} · {formatDate(item.created_at)}</small></>} />
          <ProjectRecords title="Project interventions" empty="No interventions currently recorded." records={workflow.interventions} render={(item) => <><b>{item.action}</b><span>{displayValue(item.owner_role, 'Officer owner not recorded')}</span><small>{displayValue(item.status, 'Status not recorded')} · Due {formatDate(item.due_date)}</small></>} />
          <section className="parcel-record-section officer-action"><h3>Officer action</h3><p>Interventions persist against the parent project. The selected synthetic parcel and any linked case are retained in the intervention notes.</p>{interventionMessage && <p className="form-message">{interventionMessage}</p>}{showInterventionForm ? <form className="data-form parcel-intervention-form" onSubmit={recordIntervention}><label>Officer action<textarea name="action" required /></label><label>Intervention type<input name="intervention_type" placeholder="e.g. Document review" /></label><label>Owner / responsible role<input name="owner_role" /></label><label>Status<select name="status" defaultValue="Pending"><option>Pending</option><option>In Progress</option><option>Completed</option><option>Deferred</option></select></label><label>Due date<input name="due_date" type="date" /></label><label className="span-three">Officer notes<textarea name="notes" /></label><div className="parcel-actions"><button className="primary-button" type="submit" disabled={submittingIntervention}>{submittingIntervention ? 'Saving…' : 'Save intervention'}</button><button className="text-button" type="button" onClick={() => setShowInterventionForm(false)}>Cancel</button></div></form> : <button className="primary-button" type="button" onClick={() => setShowInterventionForm(true)}>Record Intervention</button>}</section>
        </div>}
        <div className="parcel-actions"><button className="text-button" type="button" onClick={() => navigate(`/projects/${selectedProject.id}`)}>Open Project</button></div>
      </section> : <section className="panel parcel-detail-panel parcel-selection-empty"><div className="panel-heading"><div><p className="section-kicker">Parcel information</p><h2>Select a parcel</h2><p>Choose a polygon to view its acquisition workflow and parent project risk context.</p></div></div></section>}
    </section>}
  </section>
}
