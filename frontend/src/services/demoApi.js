// Browser-only demo data. This is deliberately isolated from the production API
// client so a deployed build continues to use FastAPI and PostgreSQL.

const now = '2026-09-15T10:30:00Z'
const projects = [
  {
    id: 'demo-project-1', project_code: 'BG-DEMO-001', name: 'Narmada Solar Corridor',
    project_type: 'Solar Park', state: 'Madhya Pradesh', district: 'Khandwa', village: 'Borgaon',
    current_stage: 'Compensation', status: 'Active', land_area_acres: 1250, affected_families: 318,
    villages_affected: 4, legal_disputes: 2, ownership_conflicts: 3, pending_court_cases: 1,
    documentation_completion_pct: 72, missing_documents: 18, compensation_completion_pct: 54,
    compensation_pending_cases: 94, average_compensation_delay_days: 28, rehabilitation_completion_pct: 48,
    resettlement_completion_pct: 45, affected_families_rehabilitated: 143, pending_approvals: 4,
    approval_delay_days: 21, stakeholder_response_delay_days: 14, days_in_current_stage: 86,
    possession_completion_pct: 31, historical_delay_rate: 0.42, days_remaining_to_target: 120,
    previous_stage_delay_days: 18, latitude: 21.823, longitude: 76.352, risk_category: 'Critical',
  },
  {
    id: 'demo-project-2', project_code: 'BG-DEMO-002', name: 'Eastern Freight Link',
    project_type: 'Road', state: 'Maharashtra', district: 'Nagpur', village: 'Bhiwapur',
    current_stage: 'Documentation', status: 'Active', land_area_acres: 820, affected_families: 176,
    villages_affected: 3, legal_disputes: 0, ownership_conflicts: 1, pending_court_cases: 0,
    documentation_completion_pct: 81, missing_documents: 7, compensation_completion_pct: 68,
    compensation_pending_cases: 42, average_compensation_delay_days: 12, rehabilitation_completion_pct: 67,
    resettlement_completion_pct: 65, affected_families_rehabilitated: 114, pending_approvals: 2,
    approval_delay_days: 9, stakeholder_response_delay_days: 8, days_in_current_stage: 42,
    possession_completion_pct: 57, historical_delay_rate: 0.24, days_remaining_to_target: 180,
    previous_stage_delay_days: 7, latitude: 21.1458, longitude: 79.0882, risk_category: 'High',
  },
  {
    id: 'demo-project-3', project_code: 'BG-DEMO-003', name: 'Vindhya Water Supply Scheme',
    project_type: 'Water Supply', state: 'Uttar Pradesh', district: 'Mirzapur', village: 'Chunar',
    current_stage: 'Possession', status: 'Active', land_area_acres: 460, affected_families: 92,
    villages_affected: 2, legal_disputes: 0, ownership_conflicts: 0, pending_court_cases: 0,
    documentation_completion_pct: 94, missing_documents: 1, compensation_completion_pct: 91,
    compensation_pending_cases: 6, average_compensation_delay_days: 4, rehabilitation_completion_pct: 88,
    resettlement_completion_pct: 86, affected_families_rehabilitated: 81, pending_approvals: 1,
    approval_delay_days: 3, stakeholder_response_delay_days: 3, days_in_current_stage: 23,
    possession_completion_pct: 82, historical_delay_rate: 0.12, days_remaining_to_target: 210,
    previous_stage_delay_days: 2, latitude: 25.147, longitude: 82.571, risk_category: 'Moderate',
  },
]

const predictions = {
  'demo-project-1': { id: 'demo-prediction-1', risk_score: 84.6, delay_probability: 0.846, predicted_delay_days: null, risk_category: 'Critical', model_version: '0.1.0', predicted_at: now, risk_factors: [
    { id: 'factor-1', factor_name: 'Compensation completion', impact: 0.31, direction: 'increases risk', rank: 1 },
    { id: 'factor-2', factor_name: 'Ownership conflicts', impact: 0.21, direction: 'increases risk', rank: 2 },
    { id: 'factor-3', factor_name: 'Pending approvals', impact: 0.17, direction: 'increases risk', rank: 3 },
  ] },
  'demo-project-2': { id: 'demo-prediction-2', risk_score: 68.2, delay_probability: 0.682, predicted_delay_days: null, risk_category: 'High', model_version: '0.1.0', predicted_at: now, risk_factors: [] },
  'demo-project-3': { id: 'demo-prediction-3', risk_score: 38.4, delay_probability: 0.384, predicted_delay_days: null, risk_category: 'Moderate', model_version: '0.1.0', predicted_at: now, risk_factors: [] },
}

const alerts = [
  { id: 'demo-alert-1', project_id: 'demo-project-1', alert_type: 'ML: Compensation risk', severity: 'Critical', message: 'Compensation completion is below the expected threshold for this stage.', acknowledged: false, created_at: now },
  { id: 'demo-alert-2', project_id: 'demo-project-2', alert_type: 'ML: Documentation risk', severity: 'High', message: 'Missing land records need officer review before approval.', acknowledged: false, created_at: now },
]
const recommendations = [
  { id: 'demo-recommendation-1', project_id: 'demo-project-1', title: 'ML: Compensation', description: 'Action: Prioritize unresolved compensation cases and schedule a village review camp.', priority: 'High', status: 'Pending' },
  { id: 'demo-recommendation-2', project_id: 'demo-project-2', title: 'ML: Documentation', description: 'Action: Complete title verification for the remaining land parcels.', priority: 'High', status: 'In Progress' },
]
const interventions = [
  { id: 'demo-intervention-1', project_id: 'demo-project-1', action: 'Hold compensation review camp', intervention_type: 'Community coordination', owner_role: 'District Officer', due_date: '2026-09-22', status: 'In Progress', notes: 'Village notice issued.' },
]
const cases = [
  { id: 'demo-case-1', project_id: 'demo-project-1', case_number: 'LC-2026-014', title: 'Ownership verification for parcel cluster B', case_type: 'Ownership', status: 'Open', priority: 'High', description: 'Verify competing ownership documents.', created_at: now, updated_at: now },
]

function clone(value) { return structuredClone(value) }
function projectById(id) { return projects.find((project) => project.id === id) }
function json(data) { return new Response(JSON.stringify(data), { headers: { 'Content-Type': 'application/json' } }) }
function parseBody(options) { try { return options?.body ? JSON.parse(options.body) : {} } catch { return {} } }
function summary() {
  return {
    total_projects: projects.length, active_projects: projects.filter((item) => item.status === 'Active').length,
    high_critical_risk_projects: 2, open_alerts: alerts.filter((item) => !item.acknowledged).length,
    active_cases: cases.filter((item) => item.status === 'Open').length, delayed_projects: 2,
    risk_distribution: [{ label: 'Critical', value: 1 }, { label: 'High', value: 1 }, { label: 'Moderate', value: 1 }, { label: 'Low', value: 0 }],
    projects_by_district: [{ label: 'Khandwa', value: 1 }, { label: 'Nagpur', value: 1 }, { label: 'Mirzapur', value: 1 }],
    status_distribution: [{ label: 'Active', value: 3 }], stage_distribution: [{ label: 'Compensation', value: 1 }, { label: 'Documentation', value: 1 }, { label: 'Possession', value: 1 }],
    project_creation_trend: [{ period: 'Sep 2026', value: 3 }],
  }
}

export function demoResponse(path, options = {}) {
  const method = options.method || 'GET'
  const body = parseBody(options)
  const cleanPath = path.split('?')[0]
  if (cleanPath === '/auth/status') return json({ auth_required: false, demo_mode: true })
  if (cleanPath === '/auth/login') return json({ access_token: 'demo-access-token', token_type: 'bearer', name: 'Demo Officer' })
  if (cleanPath === '/auth/me') return json({ id: 'demo-user', name: 'Demo Officer', email: 'demo@bhoomiguard.local', role: 'officer' })
  if (cleanPath === '/projects') {
    if (method === 'POST') { const item = { ...body, id: `demo-project-${Date.now()}`, project_code: body.project_code || 'BG-DEMO-NEW', risk_category: 'Unassessed' }; projects.push(item); return json(clone(item)) }
    return json(clone(projects))
  }
  if (cleanPath === '/analytics/overview') return json(summary())
  if (cleanPath === '/analytics/attention') return json(clone(projects.slice(0, 2).map((project) => ({ ...project, ...predictions[project.id], bottleneck: project.id === 'demo-project-1' ? 'Compensation completion' : 'Missing documentation' }))))
  if (cleanPath === '/gis/projects') return json(clone(projects))
  if (cleanPath === '/alerts') return json(clone(alerts))
  if (cleanPath === '/recommendations') return json(clone(recommendations))
  if (cleanPath === '/interventions') {
    if (method === 'POST') { const item = { ...body, id: `demo-intervention-${Date.now()}` }; interventions.push(item); return json(clone(item)) }
    return json(clone(interventions))
  }
  if (cleanPath === '/cases') return json(clone(cases))
  if (cleanPath === '/integrations/status') return json({ ml_service_configured: true, copilot_service_configured: false, demo_mode: true })
  const detailMatch = cleanPath.match(/^\/projects\/([^/]+)\/detail$/)
  if (detailMatch) { const project = projectById(detailMatch[1]); return json(project ? { project: clone(project), latest_prediction: clone(predictions[project.id] || null), recommendations: clone(recommendations.filter((item) => item.project_id === project.id)), alerts: clone(alerts.filter((item) => item.project_id === project.id)), interventions: clone(interventions.filter((item) => item.project_id === project.id)) } : null) }
  const whatIfMatch = cleanPath.match(/^\/projects\/([^/]+)\/what-if$/)
  if (whatIfMatch) { const baseline = predictions[whatIfMatch[1]] || predictions['demo-project-3']; const improvement = (Number(body.documentation_completion_pct || 0) + Number(body.compensation_completion_pct || 0)) / 10 + Number(body.pending_approvals || 0) * 2; const score = Math.max(5, Math.round((baseline.risk_score - improvement) * 10) / 10); const category = score >= 75 ? 'Critical' : score >= 50 ? 'High' : score >= 25 ? 'Moderate' : 'Low'; return json({ baseline: { risk_score: baseline.risk_score, risk_category: baseline.risk_category }, scenario: { risk_score: score, risk_category: category }, impact: { risk_score_change_percentage_points: Math.round((score - baseline.risk_score) * 10) / 10 }, interpretation: 'Demo scenario: improving completion indicators reduces the estimated risk score.', duration_note: 'The prototype does not predict delay duration.' }) }
  const refreshMatch = cleanPath.match(/^\/projects\/([^/]+)\/predictions\/refresh$/)
  if (refreshMatch) return json(clone(predictions[refreshMatch[1]] || predictions['demo-project-3']))
  const projectMatch = cleanPath.match(/^\/projects\/([^/]+)$/)
  if (projectMatch) { const project = projectById(projectMatch[1]); if (method === 'PUT' && project) Object.assign(project, body); return json(clone(project || null)) }
  const alertMatch = cleanPath.match(/^\/alerts\/([^/]+)\/acknowledge$/)
  if (alertMatch) { const alert = alerts.find((item) => item.id === alertMatch[1]); if (alert) alert.acknowledged = true; return json(clone(alert)) }
  const recommendationMatch = cleanPath.match(/^\/recommendations\/([^/]+)$/)
  if (recommendationMatch) { const item = recommendations.find((value) => value.id === recommendationMatch[1]); if (item) Object.assign(item, body); return json(clone(item)) }
  const interventionMatch = cleanPath.match(/^\/interventions\/([^/]+)$/)
  if (interventionMatch) { const item = interventions.find((value) => value.id === interventionMatch[1]); if (item) Object.assign(item, body); return json(clone(item)) }
  if (cleanPath.startsWith('/reports/')) return new Response('BhoomiGuard AI demo report\nThis document is generated from local demonstration data.', { headers: { 'Content-Type': 'application/pdf' } })
  return json([])
}
