import { Icon } from './Icon'

export function PageState({ loading, error, empty, children, emptyIcon = 'projects', emptyTitle = 'No data is available yet.', emptyDescription = 'This view will populate from the connected BhoomiGuard API as records are added.' }) {
  if (loading) return <div className="state-panel" role="status" aria-live="polite"><Icon name="clock" size={25} /><b>Loading live information…</b></div>
  if (error) return <div className="state-panel error" role="alert"><Icon name="warning" size={25} /><b>Unable to load this information.</b><p>{typeof error === 'string' ? error : 'Please try again.'}</p></div>
  if (empty) return <div className="state-panel"><Icon name={emptyIcon} size={25} /><b>{emptyTitle}</b><p>{emptyDescription}</p></div>
  return children
}
