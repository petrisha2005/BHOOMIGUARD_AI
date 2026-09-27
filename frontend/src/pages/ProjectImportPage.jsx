import { useState } from 'react'
import { Badge } from '../components/Badge'
import { Icon } from '../components/Icon'
import { PageTitle } from '../components/PageTitle'
import { navigate } from '../router'
import { importAndAnalyzeProjects, previewProjectImport } from '../services/bhoomiApi'
import { parseCsv } from '../utils/csv'

const requiredColumns = ['project_code', 'name']

function BatchResults({ batch }) {
  if (!batch) return null
  return <section className="panel batch-results" aria-live="polite">
    <div className="panel-heading"><div><p className="section-kicker">Batch analysis</p><h2>ML Analysis Complete</h2><p>{batch.processed_projects} of {batch.total_projects} project{batch.total_projects === 1 ? '' : 's'} analysed. {batch.failed_projects} failed.</p></div><Icon name="analytics" size={20} /></div>
    <div className="table-wrap"><table><thead><tr><th>Project</th><th>Risk score</th><th>Risk band</th><th>Recommendations</th><th>Alerts</th><th>Status</th></tr></thead><tbody>{batch.results.map((result) => <tr key={result.project_id}><td><button className="text-button" type="button" onClick={() => navigate(`/projects/${result.project_id}`)}>{result.name}<small>{result.project_code}</small></button></td><td>{result.risk_score == null ? '—' : Number(result.risk_score).toFixed(2)}</td><td>{result.risk_category ? <Badge type="risk" value={result.risk_category} /> : '—'}</td><td>{result.recommendation_count}</td><td>{result.alert_count}</td><td>{result.error ? <span className="batch-error">{result.error}</span> : <Badge value={result.status} />}</td></tr>)}</tbody></table></div>
  </section>
}

export function ProjectImportPage() {
  const [fileName, setFileName] = useState('')
  const [rows, setRows] = useState([])
  const [preview, setPreview] = useState(null)
  const [batch, setBatch] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function selectFile(event) {
    const file = event.target.files?.[0]
    setPreview(null); setBatch(null); setError(''); setRows([])
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.csv')) { setError('Choose a CSV file. Excel files are not imported by this workflow.'); return }
    try {
      const parsed = parseCsv(await file.text())
      const missing = requiredColumns.filter((column) => !parsed.headers.includes(column))
      if (missing.length) throw new Error(`Missing required CSV columns: ${missing.join(', ')}.`)
      if (!parsed.rows.length) throw new Error('The CSV has no project rows to validate.')
      setFileName(file.name); setRows(parsed.rows); setBusy(true)
      setPreview(await previewProjectImport(parsed.rows))
    } catch (fileError) { setError(fileError.message) } finally { setBusy(false) }
  }

  async function acceptAndAnalyzeRows() {
    if (!preview || preview.invalid_rows || !rows.length) return
    try {
      setBusy(true); setError('')
      setBatch(await importAndAnalyzeProjects(rows))
      setRows([]); setPreview(null)
    } catch (requestError) { setError(requestError.message) } finally { setBusy(false) }
  }

  return <section className="page-content"><PageTitle title="Import Projects from CSV" description="Validate CSV data, then import every accepted project and run the existing ML analysis in one batch." action={<button className="secondary-button" type="button" onClick={() => navigate('/projects')}><Icon name="arrowLeft" size={16} />Projects</button>} /><section className="import-layout"><article className="panel import-intro"><Icon name="upload" size={28} /><h2>CSV-first batch analysis</h2><p>The CSV must include <code>project_code</code>, <code>name</code>, and all 26 canonical ML feature columns. Every row is validated before any project is imported.</p><p><b>Historical delay rate:</b> use a decimal from 0 to 1; for example, <code>0.25</code> means 25%.</p><label className="file-picker"><Icon name="upload" />Choose CSV<input type="file" accept=".csv,text/csv" onChange={selectFile} /></label>{fileName && <small>Selected: {fileName}</small>}</article><article className="panel import-preview"><h2>Validation preview</h2>{busy && <div className="inline-loading">{preview ? 'Running ML analysis…' : 'Validating CSV rows…'}</div>}{error && <div className="notice error"><Icon name="warning" />{error}</div>}{preview && <><div className="import-summary"><span><b>{preview.valid_rows}</b> valid rows</span><span className={preview.invalid_rows ? 'bad' : 'good'}><b>{preview.invalid_rows}</b> invalid rows</span></div>{preview.errors.length > 0 && <div className="table-wrap"><table><thead><tr><th>CSV row</th><th>Field</th><th>Issue</th></tr></thead><tbody>{preview.errors.map((item, index) => <tr key={`${item.row_number}-${item.field}-${index}`}><td>{item.row_number}</td><td><code>{item.field}</code></td><td>{item.message}</td></tr>)}</tbody></table></div>}{preview.preview.length > 0 && <div className="table-wrap preview-table"><table><thead><tr><th>Project code</th><th>Project name</th><th>District</th><th>Stage</th></tr></thead><tbody>{preview.preview.map((project) => <tr key={project.project_code}><td>{project.project_code}</td><td>{project.name}</td><td>{project.district || '—'}</td><td>{project.current_stage || '—'}</td></tr>)}</tbody></table></div>}<button className="primary-button" type="button" onClick={acceptAndAnalyzeRows} disabled={busy || preview.invalid_rows > 0 || preview.valid_rows === 0}><Icon name="analytics" size={16} />Accept &amp; Run ML Analysis</button>{preview.invalid_rows > 0 && <p className="form-message">Correct the invalid rows and select the CSV again. No rows have been imported or analysed.</p>}</>}</article></section><BatchResults batch={batch} /></section>
}
