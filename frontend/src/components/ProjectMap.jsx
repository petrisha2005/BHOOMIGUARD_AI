import { useEffect, useRef, useState } from 'react'
import { navigate } from '../router'

const MAPLIBRE_CSS = 'https://unpkg.com/maplibre-gl@5.12.0/dist/maplibre-gl.css'
const MAPLIBRE_JS = 'https://unpkg.com/maplibre-gl@5.12.0/dist/maplibre-gl.js'
const PARCEL_SOURCE = 'bhoomiguard-parcels'
const CORRIDOR_SOURCE = 'bhoomiguard-corridor'

function loadMapLibre() {
  if (window.maplibregl) return Promise.resolve(window.maplibregl)
  return new Promise((resolve, reject) => {
    if (!document.querySelector(`link[href="${MAPLIBRE_CSS}"]`)) { const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = MAPLIBRE_CSS; document.head.appendChild(link) }
    const script = document.createElement('script'); script.src = MAPLIBRE_JS; script.onload = () => resolve(window.maplibregl); script.onerror = () => reject(new Error('Map library could not be loaded.')); document.head.appendChild(script)
  })
}

function markerColor(risk) { return ({ Critical: '#bd3d3d', High: '#c77c20', Moderate: '#aa8523' })[risk] || '#356b95' }
function emptyFeatureCollection() { return { type: 'FeatureCollection', features: [] } }
function isPolygon(geometry) { return geometry?.type === 'Polygon' && Array.isArray(geometry.coordinates) && geometry.coordinates.length > 0 }
function isLineString(geometry) { return geometry?.type === 'LineString' && Array.isArray(geometry.coordinates) && geometry.coordinates.length >= 2 }

export function corridorFeatureCollection(project) {
  if (!project || !isLineString(project.corridor_geometry)) return emptyFeatureCollection()
  return { type: 'FeatureCollection', features: [{ type: 'Feature', geometry: project.corridor_geometry, properties: { project_code: project.project_code, label: 'Synthetic infrastructure corridor' } }] }
}

export function parcelFeatureCollection(parcels, selectedParcelId) {
  return { type: 'FeatureCollection', features: parcels.filter((parcel) => isPolygon(parcel.geometry)).map((parcel) => ({
    type: 'Feature', id: parcel.id, geometry: parcel.geometry,
    properties: { parcel_id: parcel.parcel_id, ownership_type: parcel.ownership_type, acquisition_status: parcel.acquisition_status, area_acres: Number(parcel.area_acres), acquisition_case_id: parcel.acquisition_case_id || '', risk_category: parcel.latest_project_risk?.risk_category || 'Unassessed', risk_probability: parcel.latest_project_risk?.delay_probability == null ? null : Number(parcel.latest_project_risk.delay_probability), selected: parcel.id === selectedParcelId },
  })) }
}

function addParcelLayers(map, onParcelSelectRef) {
  if (map.getSource(PARCEL_SOURCE)) return
  map.addSource(CORRIDOR_SOURCE, { type: 'geojson', data: emptyFeatureCollection() })
  map.addLayer({ id: 'corridor-outline', type: 'line', source: CORRIDOR_SOURCE, paint: { 'line-color': '#f4e2a5', 'line-width': 12, 'line-opacity': 0.88 } })
  map.addLayer({ id: 'corridor-line', type: 'line', source: CORRIDOR_SOURCE, paint: { 'line-color': '#76552f', 'line-width': 4, 'line-opacity': 0.95, 'line-dasharray': [2, 1] } })
  map.addSource(PARCEL_SOURCE, { type: 'geojson', data: emptyFeatureCollection() })
  map.addLayer({ id: 'parcel-fill', type: 'fill', source: PARCEL_SOURCE, paint: { 'fill-color': ['match', ['get', 'ownership_type'], 'GOVERNMENT', '#4f7d58', 'PRIVATE', '#b77835', '#6f8190'], 'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.74, ['boolean', ['get', 'selected'], false], 0.68, 0.42] } })
  map.addLayer({ id: 'parcel-outline', type: 'line', source: PARCEL_SOURCE, paint: { 'line-color': ['match', ['get', 'acquisition_status'], 'ACQUIRED', '#2c704c', 'DISPUTED', '#ad3e3e', 'ON_HOLD', '#8b622a', 'IN_PROGRESS', '#236b8c', '#68737a'], 'line-width': ['case', ['boolean', ['feature-state', 'hover'], false], 3, ['boolean', ['get', 'selected'], false], 3, 1.5] } })
  let hoveredId = null
  map.on('mouseenter', 'parcel-fill', () => { map.getCanvas().style.cursor = 'pointer' })
  map.on('mouseleave', 'parcel-fill', () => { map.getCanvas().style.cursor = ''; if (hoveredId !== null) map.setFeatureState({ source: PARCEL_SOURCE, id: hoveredId }, { hover: false }); hoveredId = null })
  map.on('mousemove', 'parcel-fill', (event) => { const feature = event.features?.[0]; if (!feature || feature.id === hoveredId) return; if (hoveredId !== null) map.setFeatureState({ source: PARCEL_SOURCE, id: hoveredId }, { hover: false }); hoveredId = feature.id; map.setFeatureState({ source: PARCEL_SOURCE, id: hoveredId }, { hover: true }) })
  map.on('click', 'parcel-fill', (event) => { const feature = event.features?.[0]; if (feature?.id) onParcelSelectRef.current?.(String(feature.id)) })
}

export function ProjectMap({ projects, parcels, selectedProjectId, selectedParcelId, onProjectSelect, onParcelSelect, onError }) {
  const mapElement = useRef(null); const map = useRef(null); const markers = useRef([]); const onParcelSelectRef = useRef(onParcelSelect); const [ready, setReady] = useState(false)
  useEffect(() => { onParcelSelectRef.current = onParcelSelect }, [onParcelSelect])
  useEffect(() => { let cancelled = false; loadMapLibre().then((maplibregl) => { if (cancelled || !mapElement.current) return; map.current = new maplibregl.Map({ container: mapElement.current, style: { version: 8, sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } }, layers: [{ id: 'osm', type: 'raster', source: 'osm' }] }, center: [78.9629, 22.5937], zoom: 4.2 }); map.current.addControl(new maplibregl.NavigationControl(), 'top-right'); map.current.on('load', () => { addParcelLayers(map.current, onParcelSelectRef); setReady(true) }); map.current.on('error', () => onError('The map basemap could not be loaded. Check your network connection and try again.')) }).catch((error) => onError(error.message)); return () => { cancelled = true; markers.current.forEach((marker) => marker.remove()); markers.current = []; map.current?.remove(); map.current = null; setReady(false) } }, [onError])
  useEffect(() => { if (!ready || !map.current || !window.maplibregl) return; const maplibregl = window.maplibregl; markers.current.forEach((marker) => marker.remove()); markers.current = []; const mappedProjects = projects.map((project) => ({ project, latitude: Number(project.latitude), longitude: Number(project.longitude) })).filter(({ latitude, longitude }) => Number.isFinite(latitude) && Number.isFinite(longitude)); mappedProjects.forEach(({ project, latitude, longitude }) => { const popupContent = document.createElement('div'); popupContent.className = 'project-map-popup'; const title = document.createElement('strong'); title.textContent = project.name || project.project_code; const details = document.createElement('p'); details.textContent = [project.project_code, project.district, project.current_stage].filter(Boolean).join(' · '); const status = document.createElement('p'); status.textContent = `Status: ${project.status || 'Not recorded'} | Risk: ${project.risk_category || 'Unassessed'}`; const parcelButton = document.createElement('button'); parcelButton.type = 'button'; parcelButton.textContent = isLineString(project.corridor_geometry) ? 'View corridor & parcels' : 'View parcels'; parcelButton.addEventListener('click', () => onProjectSelect(project)); const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Open project'; button.addEventListener('click', () => navigate(`/projects/${project.id}`)); popupContent.append(title, details, status, parcelButton, button); const marker = new maplibregl.Marker({ color: markerColor(project.risk_category) }).setLngLat([longitude, latitude]).setPopup(new maplibregl.Popup({ offset: 24 }).setDOMContent(popupContent)).addTo(map.current); markers.current.push(marker) }); const firstLocation = mappedProjects[0]; if (firstLocation && !selectedProjectId) { const bounds = new maplibregl.LngLatBounds([firstLocation.longitude, firstLocation.latitude], [firstLocation.longitude, firstLocation.latitude]); mappedProjects.slice(1).forEach(({ latitude, longitude }) => bounds.extend([longitude, latitude])); map.current.fitBounds(bounds, { padding: 56, maxZoom: 11 }) } }, [projects, ready, selectedProjectId, onProjectSelect])
  useEffect(() => { if (!ready || !map.current) return; map.current.getSource(PARCEL_SOURCE)?.setData(parcelFeatureCollection(parcels, selectedParcelId)) }, [parcels, ready, selectedParcelId])
  useEffect(() => { if (!ready || !map.current) return; const project = projects.find((item) => item.id === selectedProjectId); map.current.getSource(CORRIDOR_SOURCE)?.setData(corridorFeatureCollection(project)) }, [projects, ready, selectedProjectId])
  useEffect(() => { if (!ready || !map.current || !selectedProjectId) return; const project = projects.find((item) => item.id === selectedProjectId); if (project?.latitude != null && project?.longitude != null) map.current.flyTo({ center: [Number(project.longitude), Number(project.latitude)], zoom: Math.max(map.current.getZoom(), 14), essential: true }) }, [projects, ready, selectedProjectId])
  return <div className="map-canvas" ref={mapElement} aria-label="OpenStreetMap project and synthetic parcel map" />
}
