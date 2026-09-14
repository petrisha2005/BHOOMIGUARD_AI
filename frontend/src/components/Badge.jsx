import { displayValue, slug } from '../utils/formatters'

export function Badge({ value, type = 'status' }) {
  return <span className={`badge ${type}-${slug(value)}`}>{displayValue(value, 'Unassessed')}</span>
}
