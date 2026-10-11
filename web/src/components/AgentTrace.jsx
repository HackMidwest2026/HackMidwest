import { useEffect, useRef, useState } from 'react'

export const AGENT_STYLE = {
  pipeline: { label: 'Pipeline', chip: 'bg-[#00236F] text-white', bar: 'border-l-[#00236F]' },
  intake: { label: 'Intake', chip: 'bg-purple-600 text-white', bar: 'border-l-purple-500' },
  dedup: { label: 'Dedup', chip: 'bg-[#0D9488] text-white', bar: 'border-l-teal-500' },
  priority: { label: 'Priority', chip: 'bg-amber-500 text-white', bar: 'border-l-amber-500' },
  router: { label: 'Router', chip: 'bg-emerald-600 text-white', bar: 'border-l-emerald-500' },
  supervisor: { label: 'Supervisor', chip: 'bg-[#334155] text-white', bar: 'border-l-slate-500' },
  dispatcher: { label: 'Dispatcher', chip: 'bg-[#2563EB] text-white', bar: 'border-l-blue-500' },
}

const time = (ts) => new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })

/** Live agent trace log. `compact` hides timestamps for narrow panels. */
export default function AgentTrace({ events, emptyText = 'Waiting for agent activity…', compact = false, className = '', autoScroll = true }) {
  const [showTools, setShowTools] = useState(false)
  const bottom = useRef(null)
  const visible = events.filter((e) => showTools || e.status !== 'tool')
  const stepKey = (e) => `${e.run_id}|${e.agent}|${e.report_id ?? e.issue_id ?? ''}`
  const finished = new Set(events.filter((e) => e.status === 'completed' || e.status === 'error').map(stepKey))

  useEffect(() => {
    if (autoScroll) bottom.current?.scrollIntoView({ block: 'nearest' })
  }, [visible.length, autoScroll])

  return (
    <div className={`flex flex-col min-h-0 ${className}`}>
      <div className="flex items-center justify-end mb-1">
        <label className="flex items-center gap-1 text-[10px] font-mono text-slate-500 cursor-pointer">
          <input type="checkbox" checked={showTools} onChange={(e) => setShowTools(e.target.checked)} />
          TOOL CALLS
        </label>
      </div>
      <ol className="flex-1 overflow-y-auto space-y-1 pr-1">
        {visible.length === 0 && <li className="text-[11px] text-slate-400 py-2">{emptyText}</li>}
        {visible.map((e) => {
          const s = AGENT_STYLE[e.agent] || AGENT_STYLE.pipeline
          const running = e.status === 'started' && !finished.has(stepKey(e))
          return (
            <li key={e.event_id} className={`border-l-[3px] ${e.status === 'error' ? 'border-l-red-500' : s.bar} pl-2 py-1 animate-in ${e.status === 'tool' ? 'opacity-75' : ''}`}>
              <div className="flex items-center gap-1.5 text-[10px]">
                <span className={`px-1.5 rounded font-bold ${s.chip}`}>{s.label}</span>
                {running && <span className="w-2.5 h-2.5 rounded-full border-2 border-slate-200 border-t-[#2563EB] animate-spin" />}
                {e.status === 'error' && <span className="px-1 rounded bg-red-100 text-red-700 font-mono">ERROR</span>}
                {e.engine === 'bedrock' && <span className="px-1 rounded bg-emerald-100 text-emerald-800 font-mono">LLM</span>}
                {e.engine === 'fallback' && <span className="px-1 rounded bg-amber-100 text-amber-800 font-mono">FALLBACK</span>}
                {e.issue_id && <span className="px-1 rounded bg-slate-100 text-slate-600 font-mono">#{e.issue_id}</span>}
                {!compact && (
                  <span className="ml-auto font-mono text-slate-400">
                    {time(e.ts)}
                    {e.duration_ms != null && ` · ${e.duration_ms}ms`}
                  </span>
                )}
              </div>
              <div className={`mt-0.5 text-slate-700 leading-snug break-words ${e.status === 'tool' ? 'font-mono text-[10px]' : 'text-[11px]'}`}>{e.message}</div>
            </li>
          )
        })}
        <li ref={bottom} />
      </ol>
    </div>
  )
}
