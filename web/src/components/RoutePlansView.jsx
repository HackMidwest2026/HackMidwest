import { Clock, Loader2, MapPin, Route, Sparkles, Truck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { issueCode, shortAddress, tierMeta } from '../lib/display.js'
import CityMap from './CityMap.jsx'

// One colour per trip on the map and its card.
const TRIP_COLORS = ['#2563EB', '#0D9488', '#C2410C', '#7C3AED', '#DB2777', '#CA8A04', '#059669', '#DC2626', '#4F46E5', '#0891B2', '#65A30D', '#9333EA']

const minutes = (m) => (m >= 60 ? `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, '0')} m` : `${m} m`)

function Stat({ label, value, accent = 'text-slate-900' }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-3">
      <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wide">{label}</div>
      <div className={`text-xl font-bold ${accent}`}>{value}</div>
    </div>
  )
}

function TripCard({ trip, color, selected, onSelect, onOpen }) {
  return (
    <div
      onClick={onSelect}
      className={`p-4 bg-white rounded-xl border shadow-sm space-y-3 cursor-pointer transition-colors ${selected ? 'border-[#1E3A8A] ring-1 ring-[#1E3A8A]' : 'border-slate-200 hover:border-slate-300'}`}
    >
      <div className="flex items-start gap-2">
        <span className="w-2.5 h-2.5 rounded-full mt-1.5 shrink-0" style={{ background: color }} />
        <div className="min-w-0 flex-1">
          <div className="font-bold text-sm text-slate-900">{trip.headline}</div>
          <div className="text-[11px] font-mono text-slate-500 mt-0.5 flex flex-wrap gap-x-3">
            <span>
              <Truck className="w-3 h-3 inline -mt-0.5" /> {minutes(trip.drive_min)} driving
            </span>
            <span>
              <Clock className="w-3 h-3 inline -mt-0.5" /> {minutes(trip.work_min)} on site
            </span>
            <span>{trip.distance_km} km</span>
          </div>
        </div>
        {trip.over_shift && <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-rose-100 text-rose-700 shrink-0">Over shift</span>}
      </div>
      <p className="text-xs text-slate-600 leading-relaxed">{trip.reason}</p>
      <ol className="space-y-1">
        {trip.stops.map((s, n) => {
          const t = tierMeta(s.priority_tier)
          return (
            <li key={s.issue_id} className="flex items-center gap-2 text-[11px]">
              <span className="w-4 h-4 rounded-full text-white text-[9px] font-bold flex items-center justify-center shrink-0" style={{ background: color }}>
                {n + 1}
              </span>
              <span className="font-mono text-slate-400 w-12 shrink-0">+{minutes(s.arrive_min)}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onOpen(s.issue_id)
                }}
                className="font-mono font-bold text-slate-900 hover:text-[#1E3A8A] hover:underline"
              >
                {issueCode(s.issue_id)}
              </button>
              <span className={`px-1.5 rounded text-[9px] font-bold font-mono ${t.badge}`}>{t.label}</span>
              <span className="truncate text-slate-700">{shortAddress(s.address)}</span>
              {trip.ride_along_ids.includes(s.issue_id) && <span className="px-1.5 rounded text-[9px] font-semibold bg-teal-50 text-teal-700 border border-teal-200 shrink-0">ride-along</span>}
              {s.needs_approval && <span className="text-[9px] text-blue-700 shrink-0">needs approval</span>}
            </li>
          )
        })}
      </ol>
    </div>
  )
}

/** Route Planner agent: groups each crew's open jobs into one trip for today's shift. */
export default function RoutePlansView({ meta, issues, onOpen, showToast }) {
  const [plan, setPlan] = useState(null)
  const [busy, setBusy] = useState(false)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    api.routes().then((p) => p && setPlan(p)).catch(() => {})
  }, [])

  const run = async () => {
    setBusy(true)
    try {
      const p = await api.planRoutes()
      setPlan(p)
      setSelected(null)
      showToast?.('Routes planned', `${p.totals.jobs} jobs on ${p.trips.length} crew trips.`)
    } catch (err) {
      showToast?.('Route planning failed', err.message)
    } finally {
      setBusy(false)
    }
  }

  const colorOf = (crewId) => TRIP_COLORS[(plan?.trips.findIndex((t) => t.crew_id === crewId) ?? 0) % TRIP_COLORS.length]
  const shown = plan ? plan.trips.filter((t) => !selected || t.crew_id === selected) : []
  const routes = shown.map((t) => ({
    id: t.crew_id,
    color: colorOf(t.crew_id),
    points: [[t.home.lat, t.home.lng], ...t.stops.map((s) => [s.lat, s.lng]), [t.home.lat, t.home.lng]],
  }))
  const routedIds = new Set(shown.flatMap((t) => t.stops.map((s) => s.issue_id)))

  return (
    <div className="flex-1 p-6 overflow-y-auto bg-slate-50 space-y-5">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Route className="w-5 h-5 text-[#0D9488]" /> Route Plans
          </h2>
          <p className="text-xs text-slate-500">
            The Route Planner agent groups each crew's open jobs into one trip for today's 8-hour shift: urgent jobs first, nearby low-priority jobs ride along.
          </p>
        </div>
        <button
          onClick={run}
          disabled={busy}
          className="px-4 py-2 rounded-lg bg-[#1E3A8A] text-white text-sm font-semibold shadow-sm hover:bg-[#1E40AF] disabled:opacity-70 flex items-center gap-2"
        >
          {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {busy ? 'Route Planner agent is working…' : plan ? 'Re-plan routes' : 'Plan routes'}
        </button>
      </div>

      {!plan && !busy && (
        <div className="bg-white rounded-xl border border-dashed border-slate-300 p-10 text-center text-sm text-slate-500">
          <MapPin className="w-6 h-6 mx-auto mb-2 text-slate-400" />
          No plan yet. Click <span className="font-semibold text-slate-700">Plan routes</span> to have the agent build today's crew trips.
        </div>
      )}

      {plan && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <Stat label="Crew trips" value={plan.trips.length} />
            <Stat label="Jobs scheduled" value={plan.totals.jobs} />
            <Stat label="Deferred" value={plan.totals.deferred} accent={plan.totals.deferred ? 'text-amber-600' : 'text-slate-900'} />
            <Stat label="Total driving" value={minutes(plan.totals.drive_min)} />
            <Stat label="Driving saved" value={minutes(plan.totals.drive_saved_min)} accent="text-emerald-600" />
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-sm text-slate-700 leading-relaxed">
            <div className="text-[10px] font-mono text-slate-500 mb-1">
              AGENT SUMMARY · {plan.engine === 'bedrock' ? `CLAUDE (${plan.model})` : 'RULE ENGINE'} · {new Date(plan.created_at).toLocaleTimeString()}
            </div>
            {plan.summary}
            <div className="text-[11px] text-slate-500 mt-2">
              Driving saved compares this plan with sending every job as its own round trip from the crew's yard. Durations and speeds are estimates.
            </div>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            <div className="space-y-3">
              {plan.trips.map((t) => (
                <TripCard
                  key={t.crew_id}
                  trip={t}
                  color={colorOf(t.crew_id)}
                  selected={selected === t.crew_id}
                  onSelect={() => setSelected(selected === t.crew_id ? null : t.crew_id)}
                  onOpen={onOpen}
                />
              ))}
              {plan.deferred.length > 0 && (
                <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 space-y-1">
                  <div className="text-xs font-bold text-amber-800">Deferred to a later shift</div>
                  {plan.deferred.map((d) => (
                    <div key={d.issue_id} className="text-[11px] text-amber-900">
                      <button onClick={() => onOpen(d.issue_id)} className="font-mono font-bold hover:underline">
                        {issueCode(d.issue_id)}
                      </button>{' '}
                      {d.reason}
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="xl:sticky xl:top-0 h-[520px] rounded-xl overflow-hidden border border-slate-200 shadow-sm bg-white">
              <CityMap
                mode="dispatch"
                meta={meta}
                issues={issues.filter((i) => routedIds.has(i.issue_id))}
                onSelect={onOpen}
                layers={{ p1Heatmap: false, fieldTelemetry: false, wardGrid: false }}
                routes={routes}
                zoom={12}
              />
            </div>
          </div>
          <p className="text-[11px] text-slate-500">Click a trip to show only its route on the map. Click it again to show all trips.</p>
        </>
      )}
    </div>
  )
}
