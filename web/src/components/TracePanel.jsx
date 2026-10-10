import { useEffect, useRef, useState } from 'react'

export const AGENT_LABEL = {
  pipeline: 'Pipeline',
  intake: 'Intake',
  dedup: 'Dedup',
  priority: 'Priority',
  router: 'Router',
  supervisor: 'Supervisor',
  dispatcher: 'Dispatcher',
}

function time(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function TracePanel({ events, title = 'Agent trace', emptyText = 'Waiting for agent activity…', showTools: initialTools = false }) {
  const [showTools, setShowTools] = useState(initialTools)
  const bottom = useRef(null)
  const visible = events.filter((e) => showTools || e.status !== 'tool')
  const stepKey = (e) => `${e.run_id}|${e.agent}|${e.report_id ?? e.issue_id ?? ''}`
  const finished = new Set(events.filter((e) => e.status === 'completed' || e.status === 'error').map(stepKey))

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'nearest' })
  }, [visible.length])

  return (
    <section className="panel trace">
      <div className="panel-head">
        <h2>{title}</h2>
        <label className="toggle">
          <input type="checkbox" checked={showTools} onChange={(e) => setShowTools(e.target.checked)} /> tool calls
        </label>
      </div>
      <ol className="trace-list">
        {visible.length === 0 && <li className="muted">{emptyText}</li>}
        {visible.map((e) => (
          <li key={e.event_id} className={`trace-item agent-${e.agent} status-${e.status}`}>
            <div className="trace-meta">
              <span className={`chip chip-${e.agent}`}>{AGENT_LABEL[e.agent] || e.agent}</span>
              {e.status === 'started' && !finished.has(stepKey(e)) && <span className="spinner" aria-label="working" />}
              {e.status === 'error' && <span className="tag tag-error">error</span>}
              {e.engine && e.engine !== 'mock' && <span className={`tag tag-${e.engine}`}>{e.engine === 'bedrock' ? 'LLM' : 'fallback'}</span>}
              {e.issue_id && <span className="tag">#{e.issue_id}</span>}
              <span className="trace-time">
                {time(e.ts)}
                {e.duration_ms != null && ` · ${e.duration_ms} ms`}
              </span>
            </div>
            <div className={e.status === 'tool' ? 'trace-msg mono' : 'trace-msg'}>{e.message}</div>
          </li>
        ))}
        <li ref={bottom} />
      </ol>
    </section>
  )
}
