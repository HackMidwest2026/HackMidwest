import { useEffect } from 'react'
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMap, useMapEvents } from 'react-leaflet'

export const TIER_COLOR = { P1: '#c62828', P2: '#ef6c00', P3: '#f9a825', P4: '#607d8b' }

function ClickHandler({ onClick }) {
  useMapEvents({ click: (e) => onClick?.(e.latlng) })
  return null
}

function FlyTo({ target }) {
  const map = useMap()
  useEffect(() => {
    if (target) map.flyTo([target.lat, target.lng], Math.max(map.getZoom(), 15), { duration: 0.6 })
  }, [target?.lat, target?.lng]) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}

/**
 * issues: issue list to draw (sized by report count, colored by tier)
 * pin: { lat, lng } resident's dropped pin
 */
export default function IssueMap({ center, issues = [], pin, onMapClick, onSelect, selectedId, flyTo, zoom = 13, className = '' }) {
  return (
    <MapContainer center={[center.lat, center.lng]} zoom={zoom} className={`map ${className}`} scrollWheelZoom>
      <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <ClickHandler onClick={onMapClick} />
      <FlyTo target={flyTo} />
      {issues.map((i) => (
        <CircleMarker
          key={i.issue_id}
          center={[i.lat, i.lng]}
          radius={6 + Math.min(14, i.report_count * 2)}
          pathOptions={{
            color: i.issue_id === selectedId ? '#0d47a1' : '#fff',
            weight: i.issue_id === selectedId ? 4 : 2,
            fillColor: TIER_COLOR[i.priority_tier] || '#90a4ae',
            fillOpacity: ['approved', 'assigned', 'in_progress'].includes(i.status) ? 0.45 : 0.85,
          }}
          eventHandlers={{ click: () => onSelect?.(i.issue_id) }}
        >
          <Tooltip>
            <strong>
              #{i.issue_id} {i.priority_tier} · {i.priority_score}
            </strong>
            <br />
            {i.summary}
            <br />
            {i.report_count} report{i.report_count === 1 ? '' : 's'} · {i.status}
          </Tooltip>
        </CircleMarker>
      ))}
      {pin && <CircleMarker center={[pin.lat, pin.lng]} radius={10} pathOptions={{ color: '#0d47a1', weight: 3, fillColor: '#42a5f5', fillOpacity: 0.9 }} />}
    </MapContainer>
  )
}
