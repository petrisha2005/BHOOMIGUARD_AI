import { navigate, useRoute } from '../router'
import { Icon } from './Icon'

const sections = [
  { label: 'Portfolio', items: [
    ['Dashboard', 'Dashboard', '/dashboard', 'dashboard'], ['Projects', 'Projects', '/projects', 'projects'], ['Acquisition Cases', 'Cases', '/cases', 'cases'],
  ] },
  { label: 'Operations', items: [
    ['Alerts', 'Alerts', '/alerts', 'alerts'], ['Recommendations', 'Recommendations', '/recommendations', 'recommendations'], ['Interventions', 'Interventions', '/interventions', 'interventions'],
  ] },
  { label: 'Insights & tools', items: [
    ['GIS Map', 'Map', '/map', 'map'], ['Analytics', 'Analytics', '/analytics', 'analytics'], ['Reports', 'Reports', '/reports', 'reports'], ['What-If', 'What-If', '/what-if', 'whatif'],
  ] },
]

export function Sidebar() {
  const path = useRoute()
  return <aside className="sidebar">
    <button className="brand" type="button" onClick={() => navigate('/dashboard')}><span className="brand-mark" aria-hidden="true">BG</span><span><strong>BhoomiGuard AI</strong><small>Land acquisition intelligence</small></span></button>
    <nav className="sidebar-nav" aria-label="Primary navigation">
      {sections.map((section) => <section className="sidebar-section" key={section.label}><p className="nav-group-label">{section.label}</p>{section.items.map(([label, compactLabel, href, icon]) => {
        const active = path === href || (href !== '/dashboard' && path.startsWith(`${href}/`))
        return <button key={href} type="button" title={label} aria-label={label} aria-current={active ? 'page' : undefined} className={`nav-item${active ? ' active' : ''}`} onClick={() => navigate(href)}><span className="nav-icon"><Icon name={icon} size={18} /></span><span className="nav-label">{label}</span><span className="nav-label-compact">{compactLabel}</span></button>
      })}</section>)}
    </nav>
    <div className="sidebar-footer"><span className="sidebar-footer-dot" aria-hidden="true" /> <div><b>Officer workspace</b><br />Live project monitoring</div></div>
  </aside>
}
