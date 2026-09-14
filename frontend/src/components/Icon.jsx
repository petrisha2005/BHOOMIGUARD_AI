const paths = {
  dashboard: ['M4 13h6V4H4z', 'M14 20h6v-9h-6z', 'M4 20h6v-3H4z', 'M14 8h6V4h-6z'],
  projects: ['M3 7.5 5.5 4h5l2 2H20a1 1 0 0 1 1 1v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z', 'M3 9h18'],
  cases: ['M8 3h8v3H8z', 'M6 5H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-1', 'M8 12h8', 'M8 16h5'],
  alerts: ['M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9', 'M10 21h4', 'M18.5 4.5h.01'],
  recommendations: ['M7 4h10a2 2 0 0 1 2 2v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V6a2 2 0 0 1 2-2z', 'm8 10 1.5 1.5L12 8.5', 'M14 10h3', 'm8 15 1.5 1.5L12 13.5', 'M14 15h3'],
  interventions: ['m14.5 4.5 5 5', 'M4 20l4.8-1.2L19.5 8.1a2.1 2.1 0 0 0-3-3L5.8 15.8z', 'M4 20h6'],
  map: ['M9 18 3 21V6l6-3 6 3 6-3v15l-6 3z', 'M9 3v15', 'M15 6v15'],
  analytics: ['M4 19V5', 'M4 19h17', 'M8 16v-5', 'M13 16V8', 'M18 16v-9', 'm8 9 4-3 4 2 4-4'],
  reports: ['M6 3h8l4 4v14H6z', 'M14 3v5h5', 'M9 13h6', 'M9 17h4'],
  copilot: ['M12 3v4', 'M12 17v4', 'm4.2 4.2 2.8 2.8', 'm17 17 2.8 2.8', 'M3 12h4', 'M17 12h4', 'm4.2 19.8 2.8-2.8', 'm17 7 2.8-2.8', 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8z'],
  whatif: ['M4 7h10', 'M14 7h6', 'M4 17h6', 'M10 17h10', 'M11 4v6', 'M9 14v6'],
  upload: ['M12 16V3', 'm7 8 5-5 5 5', 'M5 21h14'],
  plus: ['M12 5v14', 'M5 12h14'],
  edit: ['m14.5 4.5 5 5', 'M4 20l4.8-1.2L19.5 8.1a2.1 2.1 0 0 0-3-3L5.8 15.8z'],
  eye: ['M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6-10-6-10-6', 'M12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6z'],
  logout: ['M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5', 'M14 16l4-4-4-4', 'M18 12H9'],
  user: ['M20 21a8 8 0 0 0-16 0', 'M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z'],
  arrowLeft: ['m15 18-6-6 6-6', 'M9 12h12'],
  check: ['m5 12 4 4L19 6'],
  warning: ['M12 3 2.8 20h18.4z', 'M12 9v4', 'M12 17h.01'],
  clock: ['M12 6v6l4 2', 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z'],
  external: ['M14 4h6v6', 'm20 4-9 9', 'M19 13v6a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1h6'],
  chevronDown: ['m6 9 6 6 6-6'],
  chevronRight: ['m9 18 6-6-6-6'],
  search: ['m21 21-4.35-4.35', 'M10.8 18a7.2 7.2 0 1 1 0-14.4 7.2 7.2 0 0 1 0 14.4z'],
  filter: ['M4 6h16', 'M7 12h10', 'M10 18h4'],
  location: ['M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0z', 'M12 10a2.5 2.5 0 1 0 0 .01'],
  layers: ['m12 3 9 5-9 5-9-5z', 'm3 12 9 5 9-5', 'm3 16 9 5 9-5'],
  document: ['M6 3h8l4 4v14H6z', 'M14 3v5h5', 'M9 13h6', 'M9 17h6'],
  info: ['M12 16v-4', 'M12 8h.01', 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z'],
}

export function Icon({ name, size = 18, strokeWidth = 1.8, label, className = '' }) {
  const iconPaths = paths[name] || paths.warning
  return <svg className={`app-icon ${className}`} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth} strokeLinecap="round" strokeLinejoin="round" aria-hidden={label ? undefined : 'true'} role={label ? 'img' : undefined} aria-label={label}>{label && <title>{label}</title>}{iconPaths.map((path, index) => <path d={path} key={`${name}-${index}`} />)}</svg>
}
