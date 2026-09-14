import { useCallback, useState } from 'react'
import { Icon } from '../components/Icon'
import { PageState } from '../components/PageState'
import { PageTitle } from '../components/PageTitle'
import { ProjectMap } from '../components/ProjectMap'
import { useApi } from '../hooks/useApi'
import { getMapProjects } from '../services/bhoomiApi'

export function MapPage() {
  const [mapError, setMapError] = useState('')
  const loadLocations = useCallback(() => getMapProjects(), [])
  const { data, error, loading } = useApi(loadLocations, [loadLocations])
  const projects = Array.isArray(data) ? data : []
  return <section className="page-content"><PageTitle title="GIS Project Map" description="Project markers use persisted coordinates and OpenStreetMap basemap data." /><section className="panel map-panel"><div className="map-toolbar"><span><Icon name="location" size={16} />Live project locations</span><span>{projects.length} mapped {projects.length === 1 ? 'project' : 'projects'}</span></div><div className="map-legend" aria-label="Project risk legend"><span><i className="map-dot critical" />Critical</span><span><i className="map-dot high" />High</span><span><i className="map-dot medium" />Medium</span><span><i className="map-dot unassessed" />Unassessed</span></div><PageState loading={loading} error={error || mapError} empty={!loading && !error && projects.length === 0} emptyIcon="map" emptyTitle="No mapped projects are available yet." emptyDescription="Project markers are shown only when persisted latitude and longitude are available."><ProjectMap projects={projects} onError={setMapError} /></PageState></section></section>
}
