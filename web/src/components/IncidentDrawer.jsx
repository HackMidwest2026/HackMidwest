import { Check, ChevronDown, ChevronUp, Cpu, GitFork, MapPin, Sparkles, Truck, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from '../api.js'
import { issueCode, shortAddress, slaRemaining, statusMeta, timeAgo, tierMeta } from '../lib/display.js'
import AgentTrace from './AgentTrace.jsx'
import PhotoViewer from './PhotoViewer.jsx'

const NEXT = { approved: 'in_progress', assigned: 'in_progress', in_progress: 'resolved' }

/** Floating incident console: why it's ranked, the agents' recommendation, and the human approval step. */
export default function IncidentDrawer({ issue, crews, onClose, onChangeCrew, onUpdated, showToast }) {
  const [detail, setDetail] = useState(null)
  const [showTrace, setShowTrace] = useState(false)
  const [busy, setBusy] = useState(false)
  const [viewing, setViewing] = useState(null) // index into photos, or null

  useEffect(() => {
    let cancelled = false
    api.issue(issue.issue_id).then((d) => !cancelled && setDetail(d)).catch(() => {})
    return () => {
      cancelled = true
    }
  }, [issue.issue_id, issue.report_count, issue.status, issue.priority_score])

  async function act(fn, message) {
    setBusy(true)
    try {
      const updated = await fn()
      onUpdated(updated)
      showToast(message)
    } catch (e) {
      showToast('Action failed', e.message)
    } finally {
      setBusy(false)
    }
  }

  const t = tierMeta(issue.priority_tier)
  const st = statusMeta(issue.status)
  const pending = ['new', 'triaged'].includes(issue.status)
  const crew = crews.find((c) => c.crew_id === (issue.assigned_crew || issue.recommended_crew))
  const sla = slaRemaining(issue)
  const firstReport = detail?.reports?.[0]
  const photos = (detail?.reports || []).filter((r) => r.photo_url)
  const openPhoto = (reportId) => setViewing(Math.max(0, photos.findIndex((p) => p.report_id === reportId)))

  return (
    <div className="fixed inset-x-2 bottom-2 top-[4.5rem] z-[1050] md:absolute md:inset-auto md:top-16 md:right-14 md:bottom-4 md:w-96 md:max-w-[calc(100%-4.5rem)] bg-white/95 backdrop-blur-md rounded-xl border border-slate-200 shadow-2xl text-xs animate-in flex flex-col overflow-hidden">
      <div className="p-4 pb-2 flex items-start justify-between border-b border-slate-100">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono font-bold text-sm text-slate-900">{issueCode(issue.issue_id)}</span>
            <span className={`px-1.5 rounded text-[10px] font-bold font-mono ${t.badge}`}>{t.label}</span>
            <span className={`px-1.5 rounded text-[10px] font-semibold ${st.pill}`}>{st.label}</span>
          </div>
          <div className="font-semibold text-slate-800 text-xs mt-1 leading-snug">{issue.summary}</div>
        </div>
        <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-600" aria-label="Close">
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 pt-3 space-y-2.5 text-slate-600">
        <div className="flex items-center gap-1.5 text-slate-500">
          <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="truncate">
            {shortAddress(issue.address)} · {issue.neighborhood}
          </span>
        </div>

        {issue.possible_duplicate_of && (
          <div className="p-2 bg-amber-50 rounded border border-amber-200 text-[11px] text-amber-900">
            Possible duplicate of {issueCode(issue.possible_duplicate_of)}. The Dedup agent wasn't confident enough to merge automatically.
          </div>
        )}

        {firstReport && <div className="p-2 bg-slate-50 rounded border border-slate-200/80 text-[11px] leading-relaxed italic">“{firstReport.raw_text}”</div>}

        {photos.length > 0 && (
          <div>
            <div className="text-[10px] font-mono font-bold text-slate-500 mb-1">PHOTOS ({photos.length})</div>
            <div className="flex gap-1.5 overflow-x-auto pb-1">
              {photos.map((r, i) => (
                <button
                  key={r.report_id}
                  onClick={() => setViewing(i)}
                  title={r.photo_analysis?.shows || 'Open photo'}
                  className="relative shrink-0 w-16 h-16 rounded-md overflow-hidden border border-slate-200 hover:ring-2 hover:ring-[#2563EB] focus:ring-2 focus:ring-[#2563EB] outline-none"
                >
                  <img src={r.photo_url} alt={r.photo_analysis?.shows || 'Report photo'} className="w-full h-full object-cover" loading="lazy" />
                  {r.photo_analysis?.severity && ['high', 'critical'].includes(r.photo_analysis.severity) && (
                    <span className="absolute bottom-0.5 left-0.5 px-1 rounded bg-red-600 text-white text-[8px] font-mono font-bold">{r.photo_analysis.severity.toUpperCase()}</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Priority agent */}
        <div className="p-2 bg-teal-50/70 rounded border border-teal-200/80 text-[11px]">
          <div className="flex items-center gap-1.5 text-[#0D9488] font-semibold mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>
              Priority score {issue.priority_score ?? '–'}/100 · {issue.priority_tier}
            </span>
          </div>
          <ul className="space-y-0.5">
            {issue.priority_factors?.map((f, i) => (
              <li key={i} className="flex gap-2">
                <span className={`font-mono font-bold w-8 text-right shrink-0 ${f.points >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                  {f.points >= 0 ? '+' : ''}
                  {f.points}
                </span>
                <span>{f.detail}</span>
              </li>
            ))}
          </ul>
          <div className="text-slate-500 text-[10px] mt-1.5 flex items-center gap-1">
            <GitFork className="w-3 h-3" />
            {issue.report_count > 1 ? `Auto-merged from ${issue.report_count} citizen reports` : 'Single report'} · first reported {timeAgo(issue.first_reported_at)}
          </div>
        </div>

        {/* Router agent */}
        <div className="p-2 bg-blue-50/60 rounded border border-blue-200/70 text-[11px]">
          <div className="flex items-center gap-1.5 text-[#1E3A8A] font-semibold mb-0.5">
            <Truck className="w-3.5 h-3.5" />
            <span>{issue.recommended_department_name || 'Routing…'}</span>
          </div>
          {issue.recommended_crew_name && (
            <div>
              Recommended crew: <strong>{issue.recommended_crew_name}</strong>
            </div>
          )}
          {issue.routing_reason && <div className="text-slate-500 text-[10px] mt-0.5">{issue.routing_reason}</div>}
          {sla && (
            <div className={`mt-1 font-mono text-[10px] ${sla.overdue ? 'text-rose-700 font-bold' : 'text-emerald-700'}`}>
              SLA {issue.suggested_sla_hours}h · {sla.text}
              {!sla.overdue && ' remaining'}
            </div>
          )}
        </div>

        {/* Reports */}
        {detail?.reports?.length > 1 && (
          <div>
            <div className="text-[10px] font-mono font-bold text-slate-500 mb-1">MERGED REPORTS ({detail.reports.length})</div>
            <ul className="space-y-1">
              {detail.reports.map((r) => (
                <li key={r.report_id} className="text-[11px] leading-snug">
                  <span className="font-mono text-slate-400">{timeAgo(r.created_at)}</span> “{r.raw_text}”
                  {r.photo_url && (
                    <button onClick={() => openPhoto(r.report_id)} className="text-[#2563EB] ml-1 hover:underline">
                      photo
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Audit trail */}
        <button onClick={() => setShowTrace(!showTrace)} className="w-full flex items-center justify-between text-[10px] font-mono font-bold text-slate-500 hover:text-slate-800 pt-1">
          <span className="flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5" /> AGENT AUDIT TRAIL ({detail?.agent_trace?.length ?? 0})
          </span>
          {showTrace ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
        {showTrace && <AgentTrace events={detail?.agent_trace || []} compact className="max-h-64" autoScroll={false} emptyText="No agent activity recorded." />}
      </div>

      {/* Human-in-the-loop actions */}
      <div className="p-3 border-t border-slate-100 bg-white">
        {pending ? (
          <div className="flex items-center gap-2">
            <button
              disabled={busy}
              onClick={() => act(() => api.approve(issue.issue_id, {}), `${issueCode(issue.issue_id)} approved`)}
              className="flex-1 px-2.5 py-1.5 bg-[#1E3A8A] hover:bg-[#2563EB] disabled:opacity-60 text-white rounded font-semibold text-[11px] flex items-center justify-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              Approve{crew ? `: ${crew.name.replace(/^Street Maintenance /, '')}` : ''}
            </button>
            <button disabled={busy} onClick={onChangeCrew} className="px-2.5 py-1.5 border border-slate-200 hover:bg-slate-50 rounded font-medium text-[11px] text-slate-700">
              Change crew
            </button>
            <button
              disabled={busy}
              onClick={() => act(() => api.reject(issue.issue_id, 'Not actionable'), `${issueCode(issue.issue_id)} rejected`)}
              className="px-2.5 py-1.5 border border-rose-200 text-rose-700 hover:bg-rose-50 rounded font-medium text-[11px]"
            >
              Reject
            </button>
          </div>
        ) : (
          <div className="flex items-center justify-between gap-2">
            {issue.assigned_crew_name ? (
              <div className="flex items-center gap-2 min-w-0">
                <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
                <span className="font-medium text-slate-800 truncate">{issue.assigned_crew_name}</span>
              </div>
            ) : (
              <span className="text-slate-500">{st.label}</span>
            )}
            {NEXT[issue.status] && (
              <button
                disabled={busy}
                onClick={() => act(() => api.setStatus(issue.issue_id, NEXT[issue.status]), `${issueCode(issue.issue_id)} → ${statusMeta(NEXT[issue.status]).label}`)}
                className={`px-2.5 py-1.5 text-white rounded font-semibold text-[11px] ${NEXT[issue.status] === 'resolved' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-[#1E3A8A] hover:bg-[#2563EB]'}`}
              >
                {NEXT[issue.status] === 'resolved' ? 'Mark Resolved' : 'Mark In Progress'}
              </button>
            )}
          </div>
        )}
      </div>
      {viewing != null && photos.length > 0 && createPortal(<PhotoViewer photos={photos} startIndex={viewing} onClose={() => setViewing(null)} />, document.body)}
    </div>
  )
}
