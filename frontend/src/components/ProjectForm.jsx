import { useState } from 'react'
import { Icon } from './Icon'

const fieldSections = [
  { title: 'Project Information', fields: [
    ['project_code', 'Project Code', 'text', true], ['name', 'Project Name', 'text', true], ['project_type', 'Project Type', 'text'], ['state', 'State', 'text'], ['district', 'District', 'text'], ['village', 'Village', 'text'], ['status', 'Project Status', 'text'], ['current_stage', 'Current Acquisition Stage', 'text'],
  ] },
  { title: 'Land & Affected Population', fields: [
    ['land_area_acres', 'Land Area (acres)', 'number', false, 0], ['affected_families', 'Affected Families', 'number', false, 0], ['villages_affected', 'Villages Affected', 'number', false, 0], ['latitude', 'Latitude', 'number', false, -90, 90, 'Coordinates are optional and used only for the GIS map.'], ['longitude', 'Longitude', 'number', false, -180, 180],
  ] },
  { title: 'Legal & Ownership', fields: [
    ['legal_disputes', 'Legal Disputes', 'number', false, 0], ['ownership_conflicts', 'Ownership Conflicts', 'number', false, 0], ['pending_court_cases', 'Pending Court Cases', 'number', false, 0],
  ] },
  { title: 'Documentation', fields: [
    ['documentation_completion_pct', 'Documentation Completion (%)', 'number', false, 0, 100], ['missing_documents', 'Missing Documents', 'number', false, 0],
  ] },
  { title: 'Compensation', fields: [
    ['compensation_completion_pct', 'Compensation Completion (%)', 'number', false, 0, 100], ['compensation_pending_cases', 'Compensation Pending Cases', 'number', false, 0], ['average_compensation_delay_days', 'Average Compensation Delay (days)', 'number', false, 0],
  ] },
  { title: 'Rehabilitation & Resettlement', fields: [
    ['rehabilitation_completion_pct', 'Rehabilitation Completion (%)', 'number', false, 0, 100], ['resettlement_completion_pct', 'Resettlement Completion (%)', 'number', false, 0, 100], ['affected_families_rehabilitated', 'Affected Families Rehabilitated', 'number', false, 0],
  ] },
  { title: 'Approvals & Coordination', fields: [
    ['pending_approvals', 'Pending Approvals', 'number', false, 0], ['approval_delay_days', 'Approval Delay (days)', 'number', false, 0], ['stakeholder_response_delay_days', 'Stakeholder Response Delay (days)', 'number', false, 0],
  ] },
  { title: 'Timeline & Progress', fields: [
    ['days_in_current_stage', 'Days in Current Stage', 'number', false, 0], ['possession_completion_pct', 'Possession Completion (%)', 'number', false, 0, 100], ['historical_delay_rate', 'Historical Delay Rate', 'number', false, 0, 1, 'Enter as a decimal from 0 to 1. Example: 0.25 = 25%.'], ['days_remaining_to_target', 'Days Remaining to Target', 'number', false, undefined, undefined, 'May be negative when a target date is overdue.'], ['previous_stage_delay_days', 'Previous Stage Delay (days)', 'number', false, 0],
  ] },
]

const allFields = fieldSections.flatMap((section) => section.fields)

function valuesFrom(project) {
  return Object.fromEntries(allFields.map(([name]) => [name, project?.[name] ?? '']))
}

function validate(values) {
  const errors = {}
  for (const [name, label, type, required, min, max] of allFields) {
    const value = values[name]
    if (required && !String(value).trim()) errors[name] = `${label} is required.`
    if (type === 'number' && value !== '') {
      const numeric = Number(value)
      if (Number.isNaN(numeric)) errors[name] = `${label} must be a number.`
      else if (min !== undefined && numeric < min) errors[name] = `${label} must be at least ${min}.`
      else if (max !== undefined && numeric > max) errors[name] = `${label} must be at most ${max}.`
    }
  }
  return errors
}

export function ProjectForm({ initialProject, onSave, submitting, submitLabel = 'Save project' }) {
  const [values, setValues] = useState(() => valuesFrom(initialProject))
  const [errors, setErrors] = useState({})

  function update(name, value) {
    const next = { ...values, [name]: value }
    setValues(next)
    if (errors[name]) setErrors((current) => ({ ...current, [name]: validate(next)[name] }))
  }

  async function submit(event) {
    event.preventDefault()
    const nextErrors = validate(values)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length) return
    const payload = Object.fromEntries(Object.entries(values).filter(([, value]) => value !== ''))
    await onSave(payload)
  }

  return <form className="project-form" onSubmit={submit} noValidate aria-busy={submitting}>{fieldSections.map((section) => <section className="form-section" key={section.title}><div className="form-section-heading"><h2>{section.title}</h2><p>{section.title === 'Project Information' ? 'Fields marked required establish the project record. All other information may be added as it becomes available.' : 'Optional operational inputs used by the monitoring platform and future approved ML service.'}</p></div><div className="data-form">{section.fields.map(([name, label, type, required, min, max, helper]) => <label className={`field ${errors[name] ? 'has-error' : ''}`} key={name}><span>{label} {required ? <b className="required-mark">Required</b> : <small>Optional</small>}</span><input id={name} name={name} type={type} value={values[name]} onChange={(event) => update(name, event.target.value)} onBlur={() => setErrors((current) => ({ ...current, [name]: validate(values)[name] }))} required={required} min={min} max={max} step={type === 'number' ? 'any' : undefined} aria-invalid={Boolean(errors[name])} aria-describedby={helper || errors[name] ? `${name}-help` : undefined} />{(helper || errors[name]) && <em id={`${name}-help`} className={errors[name] ? 'field-error' : 'field-helper'}>{errors[name] && <Icon name="warning" size={14} />}{errors[name] || helper}</em>}</label>)}</div></section>)}<div className="form-actions"><button className="primary-button" type="submit" disabled={submitting}>{submitting ? 'Saving…' : <><Icon name="check" size={16} />{submitLabel}</>}</button></div></form>
}
