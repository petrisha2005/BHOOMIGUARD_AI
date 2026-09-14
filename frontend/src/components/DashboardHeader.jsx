import { navigate } from '../router'
import { Icon } from './Icon'

export function DashboardHeader() {
  const name = sessionStorage.getItem('bhoomiguard_user_name') || 'Officer workspace'
  function logout() {
    sessionStorage.removeItem('bhoomiguard_access_token')
    sessionStorage.removeItem('bhoomiguard_user_name')
    navigate('/login')
  }
  return <header className="topbar">
    <span className="topbar-context">BhoomiGuard AI / Officer Console</span>
    <div className="topbar-actions"><div className="officer"><span><Icon name="user" size={16} /></span><b>{name}</b></div><button type="button" className="icon-button" aria-label="Sign out" onClick={logout}><Icon name="logout" size={17} /></button></div>
  </header>
}
