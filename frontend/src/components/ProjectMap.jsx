import { useEffect, useRef, useState } from 'react'
import { navigate } from '../router'

const MAPLIBRE_CSS = 'https://unpkg.com/maplibre-gl@5.12.0/dist/maplibre-gl.css'
const MAPLIBRE_JS = 'https://unpkg.com/maplibre-gl@5.12.0/dist/maplibre-gl.js'

function loadMapLibre() {
  if (window.maplibregl) return Promise.resolve(window.maplibregl)
  return new Promise((resolve, reject) => {
    if (!document.querySelector(`link[href="${MAPLIBRE_CSS}"]`)) { const link = document.createElement('link'); link.rel = 'stylesheet'; link.href = MAPLIBRE_CSS; document.head.appendChild(link) }
    const script = document.createElement('script'); script.src = MAPLIBRE_JS; script.onload = () => resolve(window.maplibregl); script.onerror = () => reject(new Error('Map library could not be loaded.')); document.head.appendChild(script)
  })
}

function markerColor(risk) { return ({ Critical: '#bd3d3d', High: '#c77c20', Medium: '#aa8523' })[risk] || '#356b95' }

export function ProjectMap({ projects, onError }) {
  const mapElement = useRef(null)
  const map = useRef(null)
  const markers = useRef([])
  const [ready, setReady] = useState(false)
  useEffect(() => { let cancelled = false; loadMapLibre().then((maplibregl) => { if (cancelled || !mapElement.current) return; map.current = new maplibregl.Map({ container: mapElement.current, style: { version: 8, sources: { osm: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, attribution: '© OpenStreetMap contributors' } }, layers: [{ id: 'osm', type: 'raster', source: 'osm' }] }, center: [78.9629, 22.5937], zoom: 4.2 }); map.current.addControl(new maplibregl.NavigationControl(), 'top-right'); map.current.on('load', () => setReady(true)); map.current.on('error', () => onError('The map basemap could not be loaded. Check your network connection and try again.')) }).catch((error) => onError(error.message)); return () => { cancelled = true; markers.current.forEach((marker) => marker.remove()); markers.current = []; map.current?.remove(); map.current = null; setReady(false) } }, [onError])
  useEffect(() => { if (!ready || !map.current || !window.maplibregl) return; const maplibregl = window.maplibregl; markers.current.forEach((marker) => marker.remove()); markers.current = []; const mappedProjects = projects.map((project) => ({ project, latitude: Number(project.latitude), longitude: Number(project.longitude) })).filter(({ latitude, longitude }) => Number.isFinite(latitude) && Number.isFinite(longitude)); mappedProjects.forEach(({ project, latitude, longitude }) => { const popupContent = document.createElement('div'); popupContent.className = 'project-map-popup'; const title = document.createElement('strong'); title.textContent = project.name || project.project_code; const details = document.createElement('p'); details.textContent = [project.project_code, project.district, project.current_stage].filter(Boolean).join(' · '); const status = document.createElement('p'); status.textContent = `Status: ${project.status || 'Not recorded'} | Risk: ${project.risk_category || 'Unassessed'}`; const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Open project'; button.addEventListener('click', () => navigate(`/projects/${project.id}`)); popupContent.append(title, details, status, button); const marker = new maplibregl.Marker({ color: markerColor(project.risk_category) }).setLngLat([longitude, latitude]).setPopup(new maplibregl.Popup({ offset: 24 }).setDOMContent(popupContent)).addTo(map.current); markers.current.push(marker) }); const firstLocation = mappedProjects[0]; if (firstLocation) { const bounds = new maplibregl.LngLatBounds([firstLocation.longitude, firstLocation.latitude], [firstLocation.longitude, firstLocation.latitude]); mappedProjects.slice(1).forEach(({ latitude, longitude }) => bounds.extend([longitude, latitude])); map.current.fitBounds(bounds, { padding: 56, maxZoom: 11 }) } }, [projects, ready])
  return <div className="map-canvas" ref={mapElement} aria-label="OpenStreetMap project location map" />
}
