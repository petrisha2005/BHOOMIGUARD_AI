import { Icon } from './Icon'

const cardIcons = { projects: 'projects', active: 'check', risk: 'warning', delay: 'clock' }

/** Compatibility summary card retained for existing dashboard consumers. */
export function SummaryCard({ label, value, icon = 'projects', tone = 'blue', helper }) {
  return <article className={`stat-card ${tone}`}><div className="stat-card-heading"><p>{label}</p><Icon name={cardIcons[icon] || 'projects'} size={19} /></div><strong>{value ?? '—'}</strong>{helper && <small>{helper}</small>}</article>
}
