import { DashboardHeader } from '../components/DashboardHeader'
import { Sidebar } from '../components/Sidebar'

export function AppLayout({ children }) {
  return <div className="app-shell"><Sidebar /><main className="workspace"><DashboardHeader />{children}</main></div>
}
