// City map (Leaflet + OpenStreetMap, works anywhere) rendered in the CityCare visual language: HTML markers,
// P1 heat layer, crew telemetry with dispatch vectors, neighborhood grid, and a draggable report pin.
import L from 'leaflet'
import { AlertTriangle, CheckCircle2, Crosshair, Droplets, Flame, Grid, Layers, Lightbulb, MapPin, Minus, Navigation, Plus, Truck } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { Circle, MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap, useMapEvents } from 'react-leaflet'
import { ACTIVE_WORK, categoryMeta, issueCode, OPEN_STATUSES, tierMeta } from '../lib/display.js'

function divIcon(element, anchor = 'center') {
  const shift = anchor === 'bottom' ? 'translate(-50%,-100%)' : 'translate(-50%,-50%)'
  return L.divIcon({
    className: 'cc-divicon',
    iconSize: [0, 0],
    html: `<div style="transform:${shift};width:max-content">${renderToStaticMarkup(element)}</div>`,
  })
}

// ---------- marker designs ----------

function CitizenMarker({ issue, selected }) {
  const Icon = categoryMeta(issue.category).icon
  const level = tierMeta(issue.priority_tier).level
  const color =
    issue.status === 'resolved' ? 'bg-[#059669]' : ACTIVE_WORK.has(issue.status) ? 'bg-[#2563EB]' : level === 1 ? 'bg-[#DC2626]' : level === 2 ? 'bg-[#D97706]' : 'bg-[#2563EB]'
  if (selected && issue.report_count > 1 && issue.status !== 'resolved') {
    return (
      <div className="relative flex flex-col items-center">
        <div className="absolute w-24 h-24 -top-8 rounded-full bg-red-500/15 animate-pulse" />
        <div className="whitespace-nowrap bg-[#DC2626] text-white text-[11px] font-semibold px-2.5 py-0.5 rounded shadow-md flex items-center gap-1.5 border border-red-700/30 mb-1.5">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Active Incident ({issue.report_count} reports)</span>
        </div>
        <div className="relative flex items-center justify-center w-8 h-8 rounded-md bg-[#DC2626] text-white shadow-lg border-2 border-white ring-4 ring-blue-500/40">
          <Icon className="w-5 h-5" />
        </div>
      </div>
    )
  }
  if (issue.status === 'resolved') {
    return (
      <div className="flex items-center justify-center w-7 h-7 bg-[#059669] text-white rounded-lg shadow-md border-2 border-white">
        <CheckCircle2 className="w-4 h-4 stroke-[2.5]" />
      </div>
    )
  }
  return (
    <div className={`p-1.5 rounded-full border-2 border-white shadow-md text-white ${color} ${selected ? 'ring-2 ring-blue-600 scale-125' : ''}`}>
      <Icon className="w-3 h-3" />
    </div>
  )
}

function DispatchMarker({ issue, selected }) {
  const level = tierMeta(issue.priority_tier).level
  const ring = selected ? 'ring-2 ring-[#2563EB] ring-offset-1' : ''
  if (issue.status === 'resolved') {
    return (
      <div className={`flex items-center justify-center w-6 h-6 bg-[#059669] text-white rounded-md shadow border-2 border-white ${ring}`}>
        <CheckCircle2 className="w-3.5 h-3.5" />
      </div>
    )
  }
  if (level === 1) {
    return (
      <div className="flex flex-col items-center">
        <div className={`flex items-center gap-1 bg-[#DC2626] text-white text-[10px] font-mono font-bold px-2 py-0.5 rounded shadow-md border border-red-800 whitespace-nowrap ${ring}`}>
          <AlertTriangle className="w-3 h-3" />
          <span>{issueCode(issue.issue_id)} CRITICAL P1</span>
          <span className="min-w-3.5 h-3.5 px-0.5 bg-white/30 rounded-full flex items-center justify-center text-[9px] ml-0.5">{issue.report_count}</span>
        </div>
        <div className="relative mt-1">
          <div className="w-3 h-3 bg-[#DC2626] rounded-full border-2 border-white shadow-sm" />
          <div className="absolute -inset-1 rounded-full bg-red-500/40 animate-ping" />
        </div>
      </div>
    )
  }
  if (issue.category === 'water' || issue.category === 'traffic_lighting' || level === 2) {
    const Icon = issue.category === 'water' ? Droplets : issue.category === 'traffic_lighting' ? Lightbulb : categoryMeta(issue.category).icon
    const strong = level === 2
    return (
      <div className="flex flex-col items-center">
        <div
          className={`${strong ? 'bg-[#FEF3C7] border-[#F59E0B] text-[#B45309]' : 'bg-[#FFFBEB] border-[#FDE68A] text-[#92400E]'} border text-[10px] font-mono font-bold px-1.5 py-0.5 rounded shadow-sm flex items-center gap-1 whitespace-nowrap ${ring}`}
        >
          <Icon className="w-3 h-3" />
          <span>{issueCode(issue.issue_id)}</span>
          <span className={`${strong ? 'bg-amber-200/80' : 'bg-amber-100'} px-1 rounded text-[9px]`}>{issue.report_count}</span>
        </div>
        <div className={`w-2 h-2 ${strong ? 'bg-amber-500' : 'bg-amber-400'} rounded-full mt-0.5`} />
      </div>
    )
  }
  return (
    <div className={`flex items-center gap-1 bg-white border border-slate-300 px-1.5 py-0.5 rounded shadow-sm text-[10px] font-mono text-slate-700 whitespace-nowrap ${ring}`}>
      <span>{issueCode(issue.issue_id)}</span>
      {issue.report_count > 1 && <span className="text-slate-400">×{issue.report_count}</span>}
    </div>
  )
}

function CrewBadge({ crew }) {
  const engaged = crew.active_issue_ids?.length > 0
  return engaged ? (
    <div className="flex items-center gap-1.5 bg-[#0D9488] text-white text-[11px] font-medium px-2.5 py-1 rounded shadow-lg border border-[#14B8A6] whitespace-nowrap">
      <Truck className="w-3.5 h-3.5" />
      <span className="font-semibold">{crew.name.replace(/^(Street Maintenance|Signals & Lighting|Solid Waste)\s*/, '')}:</span>
      <span>Engaged</span>
      <span className="bg-black/25 px-1.5 py-0.5 rounded text-[10px] font-mono text-[#E6FFFA]">{crew.active_issue_ids.length} job{crew.active_issue_ids.length === 1 ? '' : 's'}</span>
    </div>
  ) : (
    <div className="flex items-center gap-1.5 bg-white text-slate-800 text-[11px] font-medium px-2.5 py-1 rounded shadow-md border border-slate-300 whitespace-nowrap">
      <span className="w-2 h-2 rounded-full bg-[#059669]" />
      <span className="font-semibold">{crew.name.replace(/^(Street Maintenance|Signals & Lighting|Solid Waste)\s*/, '')}</span>
      <span className="text-slate-500">(Standby)</span>
    </div>
  )
}

function ReportPinIcon() {
  return (
    <div className="flex flex-col items-center cursor-grab">
      <div className="bg-[#1E3A8A] text-white text-[10px] font-semibold px-2 py-0.5 rounded shadow-md whitespace-nowrap mb-1 flex items-center gap-1">
        <MapPin className="w-3 h-3" />
        <span>Report Pin</span>
      </div>
      <div className="w-8 h-8 rounded-full bg-[#1E3A8A] border-2 border-white shadow-lg flex items-center justify-center text-white">
        <Navigation className="w-4 h-4 fill-white rotate-45" />
      </div>
      <div className="w-2 h-2 bg-[#1E3A8A] rotate-45 -mt-1 shadow" />
    </div>
  )
}

// ---------- marker wrappers (memoized icons) ----------

function IssueMarker({ issue, mode, selected, onSelect }) {
  const icon = useMemo(
    () => divIcon(mode === 'dispatch' ? <DispatchMarker issue={issue} selected={selected} /> : <CitizenMarker issue={issue} selected={selected} />),
    [mode, selected, issue.priority_tier, issue.status, issue.report_count, issue.category, issue.issue_id],
  )
  return (
    <Marker position={[issue.lat, issue.lng]} icon={icon} zIndexOffset={selected ? 1000 : tierMeta(issue.priority_tier).level === 1 ? 500 : 0} eventHandlers={{ click: () => onSelect?.(issue.issue_id) }}>
      {!selected && (
        <Tooltip direction="top" offset={[0, -12]}>
          <span className="font-mono font-bold">{issueCode(issue.issue_id)}</span> · {issue.summary}
        </Tooltip>
      )}
    </Marker>
  )
}

function CrewMarker({ crew, onSelect }) {
  const icon = useMemo(() => divIcon(<CrewBadge crew={crew} />), [crew.crew_id, crew.active_issue_ids?.join(','), crew.name])
  return <Marker position={[crew.home_lat, crew.home_lng]} icon={icon} eventHandlers={{ click: () => crew.active_issue_ids?.[0] && onSelect?.(crew.active_issue_ids[0]) }} />
}

function ReportPin({ pin, onMove }) {
  const icon = useMemo(() => divIcon(<ReportPinIcon />, 'bottom'), [])
  return <Marker position={[pin.lat, pin.lng]} icon={icon} draggable zIndexOffset={2000} eventHandlers={{ dragend: (e) => onMove(e.target.getLatLng()) }} />
}

// ---------- map behaviors ----------

function ClickToPin({ onPin }) {
  useMapEvents({ click: (e) => onPin?.(e.latlng) })
  return null
}

function ViewReporter({ onViewChange }) {
  const map = useMapEvents({
    moveend: () => {
      const c = map.getCenter()
      onViewChange?.({ lat: +c.lat.toFixed(5), lng: +c.lng.toFixed(5) })
    },
  })
  return null
}

/** Frame all open incidents once, so the console opens on wherever the work is. */
function FitToIssues({ issues }) {
  const map = useMap()
  const done = useRef(false)
  useEffect(() => {
    const pts = issues.filter((i) => i.lat != null && OPEN_STATUSES.has(i.status)).map((i) => [i.lat, i.lng])
    if (done.current || pts.length === 0) return
    done.current = true
    map.fitBounds(pts, { padding: [60, 60], maxZoom: 15 })
  }, [issues, map])
  return null
}

function FlyTo({ target, zoom = 15 }) {
  const map = useMap()
  useEffect(() => {
    if (target) map.flyTo([target.lat, target.lng], Math.max(map.getZoom(), zoom), { duration: 0.6 })
  }, [target?.lat, target?.lng]) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}

function HudControls({ center, onRecenter, showLayerMenu, setShowLayerMenu }) {
  const map = useMap()
  const btn = 'w-8 h-8 flex items-center justify-center text-slate-700 hover:bg-slate-100 hover:text-slate-900 border-b border-slate-200 transition-colors'
  return (
    <div
      className="absolute top-4 right-4 z-[1000] flex flex-col shadow-md rounded-lg overflow-hidden border border-slate-200/80 bg-white/90 backdrop-blur-md"
      onClick={(e) => e.stopPropagation()}
      onDoubleClick={(e) => e.stopPropagation()}
    >
      <button onClick={() => map.zoomIn()} title="Zoom in" className={btn}>
        <Plus className="w-4 h-4" />
      </button>
      <button onClick={() => map.zoomOut()} title="Zoom out" className={btn}>
        <Minus className="w-4 h-4" />
      </button>
      <button
        onClick={() => {
          map.flyTo([center.lat, center.lng], 13, { duration: 0.6 })
          onRecenter?.()
        }}
        title="Re-center"
        className={`${btn} hover:text-[#2563EB]`}
      >
        <Crosshair className="w-4 h-4" />
      </button>
      <button
        onClick={() => setShowLayerMenu(!showLayerMenu)}
        title="Map layers"
        className={`w-8 h-8 flex items-center justify-center transition-colors ${showLayerMenu ? 'bg-[#1E3A8A] text-white' : 'text-slate-700 hover:bg-slate-100'}`}
      >
        <Layers className="w-4 h-4" />
      </button>
    </div>
  )
}

export const LAYER_DEFS = [
  { key: 'p1Heatmap', label: 'P1 Heatmap', long: 'P1/P2 Heatmap Density', icon: Flame, iconClass: 'text-red-500' },
  { key: 'fieldTelemetry', label: 'Field Telemetry', long: 'Crew Telemetry & Routes', icon: Truck, iconClass: 'text-teal-600' },
  { key: 'wardGrid', label: 'Neighborhood Grid', long: 'Neighborhood Grid', icon: Grid, iconClass: 'text-slate-500' },
]

export default function CityMap({
  mode,
  meta,
  issues,
  crews = [],
  selectedId,
  onSelect,
  reportPin,
  onReportPin,
  onRecenter,
  layers,
  onToggleLayer,
  filterCategory = 'all',
  flyTo,
  zoom = 13,
  showLegend = mode === 'citizen',
  onViewChange,
  fitToIssues = false,
  routes = [],
}) {
  const [showLayerMenu, setShowLayerMenu] = useState(false)
  const visible = issues.filter(
    (i) => i.lat != null && (filterCategory === 'all' || i.category === filterCategory) && (OPEN_STATUSES.has(i.status) || i.status === 'resolved'),
  )
  const hot = visible.filter((i) => OPEN_STATUSES.has(i.status) && ['P1', 'P2'].includes(i.priority_tier))
  const byId = new Map(issues.map((i) => [i.issue_id, i]))

  return (
    <div className="relative w-full h-full">
      <MapContainer center={[meta.center.lat, meta.center.lng]} zoom={zoom} zoomControl={false} className="w-full h-full" scrollWheelZoom>
        {/* Free OpenStreetMap tiles, no API key. Softened in CSS (.cc-tiles) to match the CityCare palette. */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="cc-tiles"
          maxZoom={19}
        />
        {onReportPin && <ClickToPin onPin={onReportPin} />}
        <FlyTo target={flyTo} />
        {onViewChange && <ViewReporter onViewChange={onViewChange} />}
        {fitToIssues && <FitToIssues issues={issues} />}

        {layers.wardGrid &&
          meta.neighborhoods.map((n) => (
            <Circle key={n.name} center={[n.lat, n.lng]} radius={900} pathOptions={{ color: '#0d9488', weight: 1.5, dashArray: '6 4', fillOpacity: 0.03 }}>
              <Tooltip permanent direction="center" className="!bg-transparent !border-0 !shadow-none !text-[#0d9488] !font-bold !text-[10px] uppercase tracking-wider">
                {n.name}
              </Tooltip>
            </Circle>
          ))}

        {layers.p1Heatmap &&
          hot.map((i) => (
            <Circle
              key={`heat-${i.issue_id}`}
              center={[i.lat, i.lng]}
              radius={180 + Math.min(i.report_count, 8) * 40}
              pathOptions={{ stroke: false, fillColor: i.priority_tier === 'P1' ? '#ef4444' : '#f97316', fillOpacity: 0.18 }}
              interactive={false}
            />
          ))}

        {layers.fieldTelemetry &&
          crews.flatMap((c) =>
            (c.active_issue_ids || [])
              .map((id) => byId.get(id))
              .filter(Boolean)
              .map((i) => (
                <Polyline
                  key={`route-${c.crew_id}-${i.issue_id}`}
                  positions={[
                    [c.home_lat, c.home_lng],
                    [i.lat, i.lng],
                  ]}
                  pathOptions={{ color: '#0d9488', weight: 3.5, dashArray: '6 4', opacity: 0.8 }}
                />
              )),
          )}

        {/* Route Planner trips: yard -> stops -> yard, one colour per crew. */}
        {routes.map((r) => (
          <Polyline key={`trip-${r.id}`} positions={r.points} pathOptions={{ color: r.color, weight: 4, opacity: 0.85 }} />
        ))}
        {routes.map((r) => (
          <Circle key={`yard-${r.id}`} center={r.points[0]} radius={90} pathOptions={{ color: r.color, weight: 2, fillColor: '#fff', fillOpacity: 1 }} />
        ))}

        {visible.map((i) => (
          <IssueMarker key={i.issue_id} issue={i} mode={mode} selected={i.issue_id === selectedId} onSelect={onSelect} />
        ))}

        {layers.fieldTelemetry && crews.filter((c) => c.department_id !== 'human_review').map((c) => <CrewMarker key={c.crew_id} crew={c} onSelect={onSelect} />)}

        {reportPin && onReportPin && <ReportPin pin={reportPin} onMove={onReportPin} />}

        <HudControls center={meta.center} onRecenter={onRecenter} showLayerMenu={showLayerMenu} setShowLayerMenu={setShowLayerMenu} />
      </MapContainer>

      {showLayerMenu && onToggleLayer && (
        <div className="absolute top-4 right-14 z-[1000] bg-white/95 backdrop-blur-md border border-slate-200 rounded-lg shadow-xl p-3 w-60 text-xs text-slate-800 animate-in">
          <div className="font-semibold text-slate-900 mb-2 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[#1E3A8A]" />
            <span>Map Layers</span>
          </div>
          <div className="space-y-1">
            {LAYER_DEFS.map(({ key, long, icon: Icon, iconClass }) => (
              <label key={key} className="flex items-center justify-between cursor-pointer hover:bg-slate-50 p-1 rounded">
                <span className="flex items-center gap-1.5">
                  <Icon className={`w-3.5 h-3.5 ${iconClass}`} />
                  <span>{long}</span>
                </span>
                <input type="checkbox" checked={layers[key]} onChange={() => onToggleLayer(key)} />
              </label>
            ))}
          </div>
        </div>
      )}

      {showLegend && (
        <div className="absolute top-[9.75rem] right-4 z-[900] bg-white/90 backdrop-blur-md p-2 rounded-lg shadow-sm border border-slate-200/80 hidden sm:flex flex-col gap-1.5 text-[11px] font-medium text-slate-700 whitespace-nowrap">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#DC2626]" />
            <span>Priority Action</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#2563EB]" />
            <span>In Progress</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#059669]" />
            <span>Resolved</span>
          </div>
        </div>
      )}
    </div>
  )
}
