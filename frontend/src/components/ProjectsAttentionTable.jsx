import { Badge } from './Badge'
import { displayValue, formatRate } from '../utils/formatters'

/** Compatibility table retained for the original dashboard surface. */
export function ProjectsAttentionTable({ projects = [], isLoading, error, getRisk = (project) => project.risk_category, onViewProject }) {
  if (isLoading) return <div className="state-panel" role="status">Loading live project information…</div>
  if (error) return <div className="state-panel error" role="alert">{error}</div>
  if (projects.length === 0) return <div className="state-panel">No projects currently require attention.</div>
  return <div className="table-wrap"><table><thead><tr><th>Project</th><th>District</th><th>Stage</th><th>Risk</th><th>Delay probability</th><th /></tr></thead><tbody>{projects.map((project) => <tr key={project.id}><td><b>{project.name}</b><small>{project.project_code}</small></td><td>{displayValue(project.district, '—')}</td><td>{displayValue(project.current_stage, '—')}</td><td><Badge type="risk" value={getRisk(project)} /></td><td>{formatRate(project.delay_probability)}</td><td><button className="text-button" type="button" onClick={() => onViewProject?.(project)}>View</button></td></tr>)}</tbody></table></div>
}
