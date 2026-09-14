import { useCallback, useState } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { useApi } from '../hooks/useApi'
import { navigate } from '../router'
import { getCase, updateCase } from '../services/bhoomiApi'
import { displayValue } from '../utils/formatters'

export function CaseDetailPage({ caseId }) {
  const loadCase = useCallback(() => getCase(caseId), [caseId])
  const { data, error, loading, reload } = useApi(loadCase, [loadCase])
  const item = data && typeof data === 'object' && !Array.isArray(data) ? data : null
  const [message, setMessage] = useState('')
  async function submit(event) { event.preventDefault(); const form = new FormData(event.currentTarget); const updates = Object.fromEntries([...form.entries()].filter(([, value]) => value !== '')); try { await updateCase(caseId, updates); setMessage('Case updated.'); reload() } catch (requestError) { setMessage(requestError.message) } }
  return <section className="page-content"><PageTitle title={item ? `Case ${item.case_number}` : 'Case Detail'} description="Acquisition case status and workflow information." action={<button className="secondary-button" type="button" onClick={() => navigate('/cases')}><Icon name="arrowLeft" size={16} />All cases</button>} /><PageState loading={loading} error={error} empty={!loading && !error && !item}>{item && <div className="detail-grid"><section className="panel"><div className="panel-heading"><h2>Case status</h2><Badge value={item.case_status} /></div><div className="metric-grid compact"><div className="metric"><span>Village</span><b>{displayValue(item.village)}</b></div><div className="metric"><span>Current stage</span><b>{displayValue(item.current_stage)}</b></div><div className="metric"><span>Days pending</span><b>{displayValue(item.days_pending)}</b></div><div className="metric"><span>Documentation</span><b>{displayValue(item.documentation_status)}</b></div><div className="metric"><span>Compensation</span><b>{displayValue(item.compensation_status)}</b></div><div className="metric"><span>Dispute</span><b>{displayValue(item.dispute_status)}</b></div></div></section><section className="panel form-panel"><h2>Update case</h2><form className="data-form" onSubmit={submit}><label>Current stage<input name="current_stage" defaultValue={item.current_stage || ''} /></label><label>Case status<input name="case_status" defaultValue={item.case_status || ''} /></label><label>Documentation status<input name="documentation_status" defaultValue={item.documentation_status || ''} /></label><label>Compensation status<input name="compensation_status" defaultValue={item.compensation_status || ''} /></label><label>Dispute status<input name="dispute_status" defaultValue={item.dispute_status || ''} /></label><label>Days pending<input name="days_pending" type="number" min="0" defaultValue={item.days_pending ?? ''} /></label><button className="primary-button" type="submit">Save changes</button></form>{message && <p className="form-message">{message}</p>}</section></div>}</PageState></section>
}
