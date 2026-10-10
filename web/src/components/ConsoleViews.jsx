import { Cpu, GitFork, Play, RotateCcw, Truck } from 'lucide-react'
import { useState } from 'react'
import { api } from '../api.js'
import { categoryMeta, issueCode, OPEN_STATUSES, shortAddress, slaRemaining, statusMeta, tierMeta } from '../lib/display.js'
import AgentTrace from './AgentTrace.jsx'
import CityMap from './CityMap.jsx'

function ViewShell({ title, subtitle, right, children }) {
  return (
    <div className="flex-1 p-6 overflow-y-auto bg-slate-50 space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-lg font-bold text-slate-900">{title}</h2>
          <p className="text-xs text-slate-500">{subtitle}</p>
        </div>
        {right}
      </div>
      {children}
    </div>
  )
}

// ---------- GIS ----------

export function GisView({ meta, issues, crews, selectedId, onSelect }) {
  const open = issues.filter((i) => OPEN_STATUSES.has(i.status))
  const byHood = new Map()
  for (const i of open) {
    const h = byHood.get(i.neighborhood) || { name: i.neighborhood, total: 0, p1: 0, top: new Map() }
    h.total++
    if (i.priority_tier === 'P1') h.p1++
    h.top.set(i.category, (h.top.get(i.category) || 0) + 1)
    byHood.set(i.neighborhood, h)
  }
  const hoods = [...byHood.values()].sort((a, b) => b.p1 - a.p1 || b.total - a.total)
  return (
    <ViewShell title="GIS Spatial Density Grid" subtitle="Open incidents by neighborhood or district, with P1/P2 heat and crew telemetry">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {hoods.slice(0, 8).map((h) => {
          const [cat, n] = [...h.top.entries()].sort((a, b) => b[1] - a[1])[0]
          return (
            <div key={h.name} className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
              <div className="text-xs text-slate-500 font-mono uppercase truncate">{h.name}</div>
              <div className="text-2xl font-bold text-slate-900 mt-1">
                {h.total} Incident{h.total === 1 ? '' : 's'}
              </div>
              <div className={`text-xs font-semibold mt-1 ${h.p1 ? 'text-red-600' : 'text-slate-500'}`}>
                ● {h.p1 ? `${h.p1} P1 Critical` : `${n} ${categoryMeta(cat).label}`}
              </div>
            </div>
          )
        })}
      </div>
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <h3 className="font-bold text-slate-900 text-sm mb-3">Live Neighborhood Density Map</h3>
        <div className="h-[420px] rounded-lg overflow-hidden border border-slate-200 relative">
          <CityMap mode="dispatch" meta={meta} issues={issues} crews={crews} selectedId={selectedId} onSelect={onSelect} layers={{ p1Heatmap: true, fieldTelemetry: true, wardGrid: true }} zoom={meta.city?.default_zoom || 12} fitToIssues />
        </div>
      </div>
    </ViewShell>
  )
}

// ---------- AI pipeline ----------

const STEPS = [
  { step: 'STEP 1: INTAKE', title: 'Intake / Classifier', tier: 'Haiku-class', border: 'border-blue-200', color: 'text-[#1E3A8A]', text: 'Turns messy free text into a category, subcategory, hazard flags and confidence. Tools: list_categories, geocode_address, analyze_photo.' },
  { step: 'STEP 2: DEDUP', title: 'Duplicate Merging', tier: 'Sonnet-class', border: 'border-teal-200', color: 'text-[#0D9488]', text: 'Code finds nearby open issues by distance, time and category; the agent decides if it is the same physical problem. Low confidence goes to review.' },
  { step: 'STEP 3: PRIORITY', title: 'Hazard Risk Scoring', tier: 'Sonnet-class', border: 'border-amber-200', color: 'text-amber-700', text: 'Rubric base score (safety, road class, reports, schools/hospitals, age) plus an explained agent adjustment of up to ±15.' },
  { step: 'STEP 4: ROUTER', title: 'Department & Crew', tier: 'Sonnet-class', border: 'border-emerald-200', color: 'text-emerald-700', text: 'Recommends the department and the crew with the best balance of distance and workload, with an SLA by tier. A dispatcher approves.' },
]

export function PipelineView({ meta, stats, events, issues, onSelect, showToast, reload, clearEvents }) {
  const [busy, setBusy] = useState(null)
  const b = stats?.last_batch
  const merges = events.filter((e) => e.agent === 'dedup' && e.status === 'completed' && e.data?.duplicate_of).slice(-8).reverse()

  async function run(kind) {
    if (kind === 'reset' && !window.confirm('Reset all incidents to the seeded history?')) return
    setBusy(kind)
    try {
      if (kind === 'batch') {
        const m = await api.runDemoBatch()
        showToast(`${m.reports} reports → ${m.issues} incidents`, `${m.duplicate_reduction_pct}% duplicate reduction in ${(m.duration_ms / 1000).toFixed(1)} s`)
      } else {
        await api.resetDemo()
        clearEvents()
        showToast('Demo reset', 'Seeded history restored.')
      }
      await reload()
    } catch (e) {
      showToast('Pipeline run failed', e.message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <ViewShell
      title="Strands AI Triage Pipeline"
      subtitle={`Intake → Dedup → Priority → Router, running on the ${meta.mode === 'bedrock' ? 'Amazon Bedrock (Claude)' : 'rule-based mock'} engine`}
      right={
        <div className="flex items-center gap-2">
          <button
            onClick={() => run('batch')}
            disabled={!!busy}
            className="px-3 py-1.5 bg-[#00236F] hover:bg-[#1E3A8A] disabled:opacity-60 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm"
          >
            <Play className="w-3.5 h-3.5" />
            {busy === 'batch' ? 'Agents triaging…' : `Run demo batch (${meta.demo_report_count} reports)`}
          </button>
          <button onClick={() => run('reset')} disabled={!!busy} className="px-3 py-1.5 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg text-xs font-medium flex items-center gap-1.5">
            <RotateCcw className="w-3.5 h-3.5" /> Reset demo
          </button>
        </div>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {STEPS.map((s) => (
          <div key={s.step} className={`p-4 bg-white rounded-xl border ${s.border} shadow-sm`}>
            <div className={`text-[10px] font-mono font-bold ${s.color}`}>{s.step}</div>
            <div className="text-sm font-bold text-slate-900 mt-1">{s.title}</div>
            <div className="text-[10px] font-mono text-slate-400 mt-0.5">{meta.mode === 'bedrock' ? `Claude ${s.tier}` : 'Rule engine (mock)'}</div>
            <p className="text-xs text-slate-500 mt-1.5">{s.text}</p>
          </div>
        ))}
      </div>

      {b && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {[
            ['LAST BATCH', `${b.reports} → ${b.issues}`, 'reports → incidents'],
            ['DUPLICATE REDUCTION', `${b.duplicate_reduction_pct}%`, `${b.reports - b.issues} calls saved`],
            ['CATEGORY ACCURACY', b.ground_truth ? `${Math.round(b.ground_truth.category_accuracy * 100)}%` : '–', 'vs synthetic ground truth'],
            ['DEDUP PRECISION / RECALL', b.ground_truth ? `${Math.round(b.ground_truth.dedup_precision * 100)} / ${Math.round(b.ground_truth.dedup_recall * 100)}` : '–', 'pairwise, %'],
            ['RUN TIME', `${(b.duration_ms / 1000).toFixed(1)} s`, `${b.engine} engine`],
          ].map(([k, v, sub]) => (
            <div key={k} className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm">
              <div className="text-[10px] font-mono text-slate-500">{k}</div>
              <div className="text-2xl font-bold text-slate-900 mt-1">{v}</div>
              <div className="text-[11px] text-slate-500">{sub}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex flex-col h-[420px]">
          <h3 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-1.5">
            <Cpu className="w-4 h-4 text-[#0D9488]" /> Live Agent Trace
          </h3>
          <AgentTrace events={events} className="flex-1" />
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm h-[420px] overflow-y-auto">
          <h3 className="font-bold text-slate-900 text-sm mb-3 flex items-center gap-1.5">
            <GitFork className="w-4 h-4 text-[#0D9488]" /> Live Deduplication Event Log
          </h3>
          <div className="divide-y divide-slate-100 text-xs">
            {merges.length === 0 && <div className="py-3 text-slate-400">Merges appear here as reports come in. Run the demo batch to see a burst.</div>}
            {merges.map((e) => {
              const issue = issues.find((i) => i.issue_id === e.data.duplicate_of)
              return (
                <button key={e.event_id} onClick={() => onSelect(e.data.duplicate_of)} className="w-full text-left py-2.5 flex items-center justify-between gap-3 hover:bg-slate-50">
                  <div className="min-w-0">
                    <span className="font-mono font-bold text-[#1E3A8A]">{issueCode(e.data.duplicate_of)}</span>
                    <span className="text-slate-600 ml-2">
                      {e.report_id} merged{issue ? ` at ${shortAddress(issue.address)}` : ''}
                    </span>
                    <div className="text-[11px] text-slate-400 truncate">{e.data.reason}</div>
                  </div>
                  <span className="text-emerald-600 font-semibold font-mono text-[11px] whitespace-nowrap">conf {Math.round(e.data.confidence * 100)}%</span>
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </ViewShell>
  )
}

// ---------- Routing ----------

export function RoutingView({ issues, onOpen }) {
  const open = issues.filter((i) => OPEN_STATUSES.has(i.status))
  return (
    <ViewShell title="Routing & SLA Matrix" subtitle="Router agent recommendations, crew assignments and response deadlines by priority tier">
      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto shadow-sm">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-mono text-[11px]">
            <tr>
              <th className="p-3">INCIDENT</th>
              <th className="p-3">LOCATION</th>
              <th className="p-3">PRIORITY</th>
              <th className="p-3">DEPARTMENT</th>
              <th className="p-3">CREW</th>
              <th className="p-3">STATUS</th>
              <th className="p-3">SLA REMAINING</th>
              <th className="p-3">ACTION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {open.map((i) => {
              const sla = slaRemaining(i)
              const t = tierMeta(i.priority_tier)
              return (
                <tr key={i.issue_id} className="hover:bg-slate-50">
                  <td className="p-3 font-mono font-bold text-slate-900">{issueCode(i.issue_id)}</td>
                  <td className="p-3 text-slate-700">{shortAddress(i.address)}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono whitespace-nowrap ${t.badge}`}>{t.label}</span>
                  </td>
                  <td className="p-3 text-slate-700">{i.recommended_department_name}</td>
                  <td className="p-3 font-medium text-slate-800">
                    {i.assigned_crew_name || (i.recommended_crew_name ? <span className="text-slate-400">{i.recommended_crew_name} (rec.)</span> : <span className="text-slate-400">Unassigned</span>)}
                  </td>
                  <td className="p-3">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold whitespace-nowrap ${statusMeta(i.status).pill}`}>{statusMeta(i.status).label}</span>
                  </td>
                  <td className={`p-3 font-mono font-semibold whitespace-nowrap ${sla?.overdue ? 'text-rose-600' : 'text-emerald-600'}`}>{sla?.text ?? '–'}</td>
                  <td className="p-3">
                    <button onClick={() => onOpen(i.issue_id)} className="text-[#2563EB] hover:underline font-semibold whitespace-nowrap">
                      View Map &rarr;
                    </button>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </ViewShell>
  )
}

// ---------- Units ----------

export function UnitsView({ crews, issues, onOpen }) {
  const field = crews.filter((c) => c.department_id !== 'human_review')
  const engaged = field.filter((c) => c.active_issue_ids?.length).length
  return (
    <ViewShell
      title="Field Crews"
      subtitle="Crew workload, active CityCare assignments and home bases (simulated roster)"
      right={
        <span className="text-xs font-mono font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
          {engaged} engaged · {field.length - engaged} standby
        </span>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {field.map((c) => {
          const active = c.active_issue_ids || []
          const load = c.open_jobs / c.capacity
          return (
            <div key={c.crew_id} className="p-4 bg-white rounded-xl border border-slate-200 shadow-sm space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-bold text-sm text-slate-900 truncate">{c.name}</div>
                  <div className="text-xs text-slate-500 mt-0.5 truncate">{c.department_name}</div>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-semibold shrink-0 ${active.length ? 'bg-[#0D9488] text-white' : 'bg-slate-100 text-slate-700'}`}>
                  {active.length ? 'Engaged' : 'Standby'}
                </span>
              </div>
              <div>
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mb-1">
                  <span>WORKLOAD</span>
                  <span className="font-bold text-slate-700">
                    {c.open_jobs}/{c.capacity} jobs
                  </span>
                </div>
                <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${load >= 0.9 ? 'bg-rose-500' : load >= 0.7 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${Math.min(100, load * 100)}%` }} />
                </div>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-[11px]">
                <div className="text-slate-400 font-mono text-[10px] mb-1">CITYCARE ASSIGNMENTS</div>
                {active.length === 0 && <div className="text-slate-500">None. Available for dispatch.</div>}
                {active.map((id) => {
                  const i = issues.find((x) => x.issue_id === id)
                  return (
                    <button key={id} onClick={() => onOpen(id)} className="block w-full text-left truncate hover:text-[#1E3A8A]">
                      <span className="font-mono font-bold">{issueCode(id)}</span> {i ? `${i.summary.slice(0, 40)}${i.summary.length > 40 ? '…' : ''}` : ''}
                    </button>
                  )
                })}
              </div>
              <div className="flex justify-end">
                <button onClick={() => onOpen(active[0] ?? null)} className="text-xs font-semibold text-[#1E3A8A] hover:underline flex items-center gap-1">
                  <Truck className="w-3.5 h-3.5" /> Track on map &rarr;
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </ViewShell>
  )
}
