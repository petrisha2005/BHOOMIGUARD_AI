import { useState } from 'react'
import { Icon } from '../components/Icon'
import { PageTitle } from '../components/PageTitle'
import { navigate } from '../router'
import { importProjects, previewProjectImport } from '../services/bhoomiApi'
import { parseCsv } from '../utils/csv'

const requiredColumns = ['project_code', 'name']

export function ProjectImportPage() {
  const [fileName, setFileName] = useState('')
  const [rows, setRows] = useState([])
  const [preview, setPreview] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  async function selectFile(event) {
    const file = event.target.files?.[0]
    setPreview(null); setError(''); setMessage(''); setRows([])
    if (!file) return
    if (!file.name.toLowerCase().endsWith('.csv')) { setError('Choose a CSV file. Excel files are not imported by this workflow.'); return }
    try {
      const parsed = parseCsv(await file.text())
      const missing = requiredColumns.filter((column) => !parsed.headers.includes(column))
      if (missing.length) throw new Error(`Missing required CSV columns: ${missing.join(', ')}.`)
      if (!parsed.rows.length) throw new Error('The CSV has no project rows to validate.')
      setFileName(file.name); setRows(parsed.rows)
      setBusy(true)
      setPreview(await previewProjectImport(parsed.rows))
    } catch (fileError) { setError(fileError.message) } finally { setBusy(false) }
  }

  async function importValidatedRows() {
    if (!preview || preview.invalid_rows || !rows.length) return
    try {
      setBusy(true); setError(''); setMessage('')
      const result = await importProjects(rows)
      setMessage(`${result.created_count} project record${result.created_count === 1 ? '' : 's'} imported successfully.`)
      setRows([]); setPreview(null)
    } catch (requestError) { setError(requestError.message) } finally { setBusy(false) }
  }

  return <section className="page-content"><PageTitle title="Import Projects from CSV" description="Validate source rows against the existing BhoomiGuard project contract before any project is written." action={<button className="secondary-button" type="button" onClick={() => navigate('/projects')}><Icon name="arrowLeft" size={16} />Projects</button>} /><section className="import-layout"><article className="panel import-intro"><Icon name="upload" size={28} /><h2>CSV-first import</h2><p>Required columns: <code>project_code</code>, <code>name</code>. Additional project inputs are optional, never inferred, and are validated by the live backend contract when supplied.</p><p><b>Historical delay rate:</b> use a decimal from 0 to 1; for example, <code>0.25</code> means 25%.</p><label className="file-picker"><Icon name="upload" />Choose CSV<input type="file" accept=".csv,text/csv" onChange={selectFile} /></label>{fileName && <small>Selected: {fileName}</small>}</article><article className="panel import-preview"><h2>Validation preview</h2>{busy && <div className="inline-loading">Validating CSV rows…</div>}{error && <div className="notice error"><Icon name="warning" />{error}</div>}{message && <div className="notice success"><Icon name="check" />{message}</div>}{preview && <><div className="import-summary"><span><b>{preview.valid_rows}</b> valid rows</span><span className={preview.invalid_rows ? 'bad' : 'good'}><b>{preview.invalid_rows}</b> invalid rows</span></div>{preview.errors.length > 0 && <div className="table-wrap"><table><thead><tr><th>CSV row</th><th>Field</th><th>Issue</th></tr></thead><tbody>{preview.errors.map((item, index) => <tr key={`${item.row_number}-${item.field}-${index}`}><td>{item.row_number}</td><td><code>{item.field}</code></td><td>{item.message}</td></tr>)}</tbody></table></div>}{preview.preview.length > 0 && <div className="table-wrap preview-table"><table><thead><tr><th>Project code</th><th>Project name</th><th>District</th><th>Stage</th></tr></thead><tbody>{preview.preview.map((project) => <tr key={project.project_code}><td>{project.project_code}</td><td>{project.name}</td><td>{project.district || '—'}</td><td>{project.current_stage || '—'}</td></tr>)}</tbody></table></div>}<button className="primary-button" type="button" onClick={importValidatedRows} disabled={busy || preview.invalid_rows > 0 || preview.valid_rows === 0}><Icon name="check" size={16} />Import validated projects</button>{preview.invalid_rows > 0 && <p className="form-message">Correct the invalid rows and select the CSV again. No rows have been imported.</p>}</>}</article></section></section>
}
