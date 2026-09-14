export function StatCard({ label, value, caption, tone = 'blue', icon }) {
  return <article className={`stat-card ${tone}`}><div className="stat-card-heading"><p>{label}</p>{icon}</div><strong>{value ?? '—'}</strong>{caption && <small>{caption}</small>}</article>
}
