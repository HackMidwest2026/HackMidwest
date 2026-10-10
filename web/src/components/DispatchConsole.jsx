import { Activity, Cpu, FileText, GitFork, Grid, HeartPulse, Layers, MessageSquare, Route, Search, ShieldCheck, Truck, User } from 'lucide-react'
import { useState } from 'react'
import { issueCode, OPEN_STATUSES, shortAddress, statusMeta, timeAgo, tierMeta } from '../lib/display.js'
import CityMap, { LAYER_DEFS } from './CityMap.jsx'
import { GisView, PipelineView, RoutingView, UnitsView } from './ConsoleViews.jsx'
import IncidentDrawer from './IncidentDrawer.jsx'
import RoutePlansView from './RoutePlansView.jsx'
import { AssignModal, SupervisorModal } from './Modals.jsx'

const NAV = [
  { id: 'command', label: 'Command Center', icon: Activity, iconClass: 'text-blue-300' },
  { id: 'gis', label: 'GIS Spatial Grid', icon: Grid, iconClass: 'text-slate-400' },
  { id: 'ai-pipeline', label: 'AI Triage Pipeline', icon: Cpu, iconClass: 'text-teal-400' },
  { id: 'routing', label: 'Routing Matrix', icon: GitFork, iconClass: 'text-slate-400' },
  { id: 'units', label: 'Field Crews', icon: Truck, iconClass: 'text-slate-400' },
  { id: 'routes', label: 'Route Plans', icon: Route, iconClass: 'text-teal-400' },
]

export default function DispatchConsole({ meta, data, selectedIssue, onSelectIssue, showToast, onSwitchToCitizen }) {
  const { issues, stats, crews, events, stream, flashIds } = data
  const [view, setView] = useState('command')
  const [search, setSearch] = useState('')
  const [streamFilter, setStreamFilter] = useState('all')
  const [layers, setLayers] = useState({ p1Heatmap: true, fieldTelemetry: true, wardGrid: false })
  const [supervisorOpen, setSupervisorOpen] = useState(false)
  const [assignOpen, setAssignOpen] = useState(false)

  const open = issues.filter((i) => OPEN_STATUSES.has(i.status))
  const pending = open.filter((i) => ['new', 'triaged'].includes(i.status))
  const critical = open.filter((i) => i.priority_tier === 'P1')
  const field = crews.filter((c) => c.department_id !== 'human_review')
  const engaged = field.filter((c) => c.active_issue_ids?.length).length
  const reduction = stats?.duplicate_reduction_pct ?? 0
  const saved = stats ? stats.total_reports - stats.total_issues : 0

  const q = search.trim().toLowerCase()
  const streamList = open.filter((i) => {
    if (q && ![issueCode(i.issue_id), i.summary, i.address, i.neighborhood, i.recommended_department_name].some((s) => (s || '').toLowerCase().includes(q))) return false
    if (streamFilter === 'pending') return ['new', 'triaged'].includes(i.status)
    if (streamFilter === 'critical') return i.priority_tier === 'P1'
    return true
  })

  const openOnMap = (id) => {
    onSelectIssue(id)
    setView('command')
  }

  return (
    <div className="flex h-[calc(100vh-64px)] w-full overflow-hidden bg-[#FAF8FF]">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 bg-[#00164E] text-slate-300 hidden md:flex flex-col border-r border-[#1E3A8A] select-none">
        <div className="p-4 border-b border-blue-900/60">
          <div className="flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${stream === 'live' ? 'bg-[#0D9488] animate-pulse' : 'bg-amber-500'}`} />
            <span className="text-xs font-bold tracking-wider text-white">STRANDS AGENTS</span>
          </div>
          <div className="text-[11px] font-mono text-slate-400 mt-0.5">{meta.mode === 'bedrock' ? 'BEDROCK · CLAUDE' : 'MOCK ENGINE'}</div>
        </div>
        <nav className="flex-1 p-2 space-y-1">
          {NAV.map(({ id, label, icon: Icon, iconClass }) => (
            <button
              key={id}
              onClick={() => setView(id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-medium transition-colors ${
                view === id ? 'bg-[#1E3A8A] text-white font-semibold shadow-sm' : 'text-slate-300 hover:bg-white/5 hover:text-white'
              }`}
            >
              <span className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${iconClass}`} />
                <span>{label}</span>
              </span>
              {id === 'command' && <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0D9488] text-white">{open.length}</span>}
            </button>
          ))}
        </nav>
        <div className="p-3 border-t border-blue-900/60 text-[11px] space-y-2">
          <div>
            <div className="flex items-center justify-between text-slate-400 font-mono text-[10px] mb-1">
              <span>DUPLICATES MERGED</span>
              <span className="text-emerald-400 font-bold">{reduction}%</span>
            </div>
            <div className="w-full h-1 bg-blue-950 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${reduction}%` }} />
            </div>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400 text-[10px]">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
            <span>Human approves every dispatch</span>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="h-14 bg-white border-b border-slate-200 px-4 flex items-center justify-between shrink-0 gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-7 h-7 rounded-md bg-[#00236F] flex items-center justify-center text-white shrink-0">
              <HeartPulse className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <span className="font-bold text-slate-900 text-sm leading-tight block">CityCare Dispatch</span>
              <span className="text-[11px] text-slate-500">Kansas City Operations</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-[#FFE4E6] text-[#BE123C] px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 border border-rose-200 whitespace-nowrap">
              <span className="w-2 h-2 rounded-full bg-[#E11D48] animate-pulse" />
              <span>
                {open.length} In Queue ({critical.length} P1)
              </span>
            </div>
            <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-700 font-medium">
              <span className={`w-2 h-2 rounded-full ${stream === 'live' ? 'bg-[#059669]' : 'bg-amber-500'}`} />
              <span>{stream === 'live' ? 'Live trace synced' : 'Reconnecting…'}</span>
            </div>
            <button
              onClick={() => setSupervisorOpen(true)}
              className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-md transition-colors border border-slate-200"
            >
              <MessageSquare className="w-3.5 h-3.5 text-slate-600" />
              <span className="hidden sm:inline">Supervisor Channel</span>
              <span className="bg-[#1E3A8A] text-white rounded text-[10px] px-1 font-bold">AI</span>
            </button>
            <button
              onClick={onSwitchToCitizen}
              title="Switch to the Citizen 311 view"
              className="w-8 h-8 rounded-full bg-[#1E3A8A] text-white flex items-center justify-center hover:ring-2 hover:ring-blue-400 transition-all"
            >
              <User className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Metrics ribbon */}
        <div className="bg-[#F8FAFC] border-b border-slate-200 px-4 py-1.5 flex items-center gap-6 text-[11px] font-mono text-slate-600 overflow-x-auto shrink-0 select-none">
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <span className="font-semibold text-slate-900">LIVE INCIDENTS:</span>
            <span>
              {open.length} ({critical.length} P1 Critical)
            </span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1.5 whitespace-nowrap text-[#0D9488]">
            <GitFork className="w-3.5 h-3.5" />
            <span className="font-semibold">DUPLICATES AUTO-MERGED:</span>
            <span>
              {reduction}% ({saved} calls saved)
            </span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="flex items-center gap-1.5 whitespace-nowrap">
            <span className="font-semibold text-slate-900">AWAITING APPROVAL:</span>
            <span className={pending.length ? 'text-amber-700 font-bold' : ''}>{pending.length}</span>
          </div>
          <span className="text-slate-300">|</span>
          <div className="whitespace-nowrap text-slate-500">
            CREWS: {field.length} ({engaged} Engaged, {field.length - engaged} Standby)
          </div>
        </div>

        {/* Mobile view switcher */}
        <div className="md:hidden flex gap-1 overflow-x-auto p-2 bg-[#00164E]">
          {NAV.map(({ id, label }) => (
            <button key={id} onClick={() => setView(id)} className={`px-2.5 py-1 rounded text-[11px] whitespace-nowrap ${view === id ? 'bg-[#1E3A8A] text-white' : 'text-slate-300'}`}>
              {label}
            </button>
          ))}
        </div>

        {view === 'command' && (
          <div className="flex-1 flex overflow-hidden">
            {/* Live triage stream */}
            <div className="w-[380px] max-w-[45%] shrink-0 border-r border-slate-200 bg-white flex flex-col">
              <div className="p-3 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-slate-700" />
                  <span className="font-bold text-slate-900 text-sm">Live Triage Stream</span>
                </div>
                <span className="px-2 py-0.5 bg-blue-100 text-[#1E3A8A] text-[10px] font-mono font-bold rounded">Ranked by priority</span>
              </div>
              <div className="p-3 border-b border-slate-100 space-y-2 bg-[#FAF8FF]">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search incident, address, neighborhood…"
                    className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-md text-xs text-slate-800 placeholder-slate-400 focus:border-[#1E3A8A] outline-none"
                  />
                </div>
                <div className="flex items-center gap-1.5">
                  {[
                    ['all', `All (${open.length})`],
                    ['pending', `Needs approval (${pending.length})`],
                    ['critical', `Critical (${critical.length})`],
                  ].map(([id, label]) => (
                    <button
                      key={id}
                      onClick={() => setStreamFilter(id)}
                      className={`px-2.5 py-1 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                        streamFilter === id ? 'bg-[#1E3A8A] text-white font-semibold' : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
                {streamList.length === 0 && <div className="p-4 text-xs text-slate-400">No incidents match.</div>}
                {streamList.map((i) => {
                  const t = tierMeta(i.priority_tier)
                  const selected = selectedIssue?.issue_id === i.issue_id
                  return (
                    <div
                      key={i.issue_id}
                      onClick={() => onSelectIssue(i.issue_id)}
                      className={`p-3 cursor-pointer transition-all border-l-4 ${selected ? 'bg-blue-50/70 border-l-[#2563EB]' : `${t.border} hover:bg-slate-50`} ${
                        flashIds.has(i.issue_id) ? 'cc-flash' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between text-[11px] mb-1">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-bold text-slate-900">{issueCode(i.issue_id)}</span>
                          <span className={`px-1.5 rounded text-[10px] font-bold font-mono ${t.badge}`}>{t.label}</span>
                          <span className="font-mono font-bold text-slate-500 text-[10px]">{i.priority_score}</span>
                        </div>
                        <span className="font-mono text-slate-400 text-[10px]">{timeAgo(i.last_reported_at)}</span>
                      </div>
                      <div className="font-semibold text-slate-900 text-xs leading-snug line-clamp-2">{i.summary}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5 truncate">
                        {shortAddress(i.address)} · {i.neighborhood}
                      </div>
                      <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 pt-1.5 border-t border-slate-100 gap-2">
                        <div className="flex items-center gap-1 text-[#0D9488] font-mono text-[10px] whitespace-nowrap">
                          <GitFork className="w-3 h-3" />
                          <span>{i.report_count > 1 ? `${i.report_count} merged reports` : 'Single report'}</span>
                        </div>
                        <div className="font-mono text-[10px] truncate">
                          {['new', 'triaged'].includes(i.status) ? (
                            <span className="text-amber-700 font-semibold">• Needs approval</span>
                          ) : (
                            <span>• {i.assigned_crew_name || statusMeta(i.status).label}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Tactical map */}
            <div className="flex-1 relative min-w-0">
              <div className="absolute top-3 left-4 z-[1000] flex items-center gap-2 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-lg shadow-sm border border-slate-200 max-w-[calc(100%-6rem)] overflow-x-auto">
                <span className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5 text-slate-500" />
                  <span>Layers:</span>
                </span>
                {LAYER_DEFS.map(({ key, label, icon: Icon }) => (
                  <button
                    key={key}
                    onClick={() => setLayers((l) => ({ ...l, [key]: !l[key] }))}
                    className={`px-2.5 py-0.5 rounded text-xs font-medium flex items-center gap-1.5 whitespace-nowrap transition-colors ${
                      layers[key] ? 'bg-[#0D9488] text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    <Icon className="w-3 h-3" />
                    <span>{label}</span>
                  </button>
                ))}
              </div>
              <CityMap
                mode="dispatch"
                meta={meta}
                issues={issues}
                crews={crews}
                selectedId={selectedIssue?.issue_id}
                onSelect={onSelectIssue}
                layers={layers}
                onToggleLayer={(k) => setLayers((l) => ({ ...l, [k]: !l[k] }))}
                flyTo={selectedIssue}
                zoom={12}
              />
              {selectedIssue && (
                <IncidentDrawer
                  issue={selectedIssue}
                  crews={crews}
                  onClose={() => onSelectIssue(null)}
                  onChangeCrew={() => setAssignOpen(true)}
                  onUpdated={data.replaceIssue}
                  showToast={showToast}
                />
              )}
            </div>
          </div>
        )}

        {view === 'gis' && <GisView meta={meta} issues={issues} crews={crews} selectedId={selectedIssue?.issue_id} onSelect={openOnMap} />}
        {view === 'ai-pipeline' && (
          <PipelineView meta={meta} stats={stats} events={events} issues={issues} onSelect={openOnMap} showToast={showToast} reload={data.reload} clearEvents={data.clearEvents} />
        )}
        {view === 'routing' && <RoutingView issues={issues} onOpen={openOnMap} />}
        {view === 'units' && <UnitsView crews={crews} issues={issues} onOpen={openOnMap} />}
        {view === 'routes' && <RoutePlansView meta={meta} issues={issues} onOpen={openOnMap} showToast={showToast} />}
      </div>

      {supervisorOpen && <SupervisorModal onClose={() => setSupervisorOpen(false)} />}
      {assignOpen && selectedIssue && (
        <AssignModal issue={selectedIssue} crews={crews} onClose={() => setAssignOpen(false)} onAssigned={data.replaceIssue} showToast={showToast} />
      )}
    </div>
  )
}
