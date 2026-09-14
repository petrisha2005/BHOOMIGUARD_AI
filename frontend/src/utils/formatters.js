export function displayValue(value, fallback = 'Not available') {
  return value === null || value === undefined || value === '' ? fallback : value
}

function finiteNumber(value) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : null
}

export function formatCompletionPercent(value) {
  if (value === null || value === undefined) return 'Not available'
  const numeric = finiteNumber(value)
  return numeric === null ? 'Not available' : `${numeric.toFixed(1)}%`
}

export function formatRate(value) {
  if (value === null || value === undefined) return 'Not available'
  const numeric = finiteNumber(value)
  return numeric === null ? 'Not available' : `${(numeric * 100).toFixed(1)}%`
}

export function formatDate(value) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(value))
}

export function slug(value) {
  return String(value || 'unassessed').trim().toLowerCase().replaceAll(' ', '-')
}
