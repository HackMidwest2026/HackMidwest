import { useEffect, useState } from 'react'
import { api } from '../api.js'
import TracePanel from './TracePanel.jsx'

const NEXT_STATUS = { approved: 'in_progress', assigned: 'in_progress', in_progress: 'resolved' }

export default function IssueDetail({ issueId, meta, onClose, liveIssue }) {
  const [issue, setIssue] = useState(null)
  const [crewId, setCrewId] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  // Reload whenever the live stream says this issue changed (new report merged, re-scored...).
  useEffect(() => {
    let cancelled = false
    api
      .issue(issueId)
      .then((i) => {
        if (cancelled) return
        setIssue(i)
        setCrewId((prev) => prev || i.assigned_crew || i.recommended_crew || '')
      })
      .catch((e) => setError(e.message))
    return () => {
      cancelled = true
    }
  }, [issueId, liveIssue?.report_count, liveIssue?.status, liveIssue?.priority_score])

  if (!issue) return <section className="panel detail">{error ? <div className="banner error">{error}</div> : 'Loading…'}</section>

  const allCrews = meta.crews
  const deptCrews = allCrews.filter((c) => c.department_id === issue.recommended_department)

  async function act(fn) {
    setBusy(true)
    setError(null)
    try {
      await fn()
      setIssue(await api.issue(issueId))
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const pending = ['new', 'triaged'].includes(issue.status)
  return (
    <section className="panel detail">
      <div className="panel-head">
        <button className="link" onClick={onClose}>
          ← Queue
        </button>
        <span className={`status status-${issue.status}`}>{issue.status.replace('_', ' ')}</span>
      </div>

      <h2>
        <span className={`tier tier-${issue.priority_tier}`}>{issue.priority_tier}</span> #{issue.issue_id} · {issue.priority_score}/100
      </h2>
      <p className="detail-summary">{issue.summary}</p>
      <p className="muted">
        {issue.address} · {issue.neighborhood} · {issue.report_count} report{issue.report_count === 1 ? '' : 's'} · first reported{' '}
        {new Date(issue.first_reported_at).toLocaleDateString()}
      </p>
      {issue.possible_duplicate_of && <div className="banner warn">Possible duplicate of #{issue.possible_duplicate_of}. The dedup agent wasn't confident enough to merge.</div>}

      <h3>Why this priority</h3>
      <ul className="factors">
        {issue.priority_factors.map((f, i) => (
          <li key={i}>
            <span className={f.points >= 0 ? 'pts pos' : 'pts neg'}>
              {f.points >= 0 ? '+' : ''}
              {f.points}
            </span>
            {f.detail}
          </li>
        ))}
      </ul>

      <h3>Recommendation</h3>
      <p>
        <strong>{issue.recommended_department_name}</strong>
        {issue.recommended_crew_name && <> → {issue.recommended_crew_name}</>} · respond within {issue.suggested_sla_hours} h
      </p>
      <p className="muted">{issue.routing_reason}</p>

      {pending ? (
        <div className="approve-box">
          <label htmlFor="crew">Crew</label>
          <select id="crew" value={crewId} onChange={(e) => setCrewId(e.target.value)}>
            {(deptCrews.length ? deptCrews : allCrews).map((c) => (
              <option key={c.crew_id} value={c.crew_id}>
                {c.name} ({c.open_jobs}/{c.capacity})
              </option>
            ))}
            <optgroup label="Other departments">
              {allCrews
                .filter((c) => !deptCrews.includes(c))
                .map((c) => (
                  <option key={c.crew_id} value={c.crew_id}>
                    {c.name}
                  </option>
                ))}
            </optgroup>
          </select>
          <input placeholder="Note (optional)" value={note} onChange={(e) => setNote(e.target.value)} />
          <div className="row">
            <button className="primary" disabled={busy} onClick={() => act(() => api.approve(issue.issue_id, { crew_id: crewId || undefined, note }))}>
              {crewId && crewId !== issue.recommended_crew ? 'Edit & approve' : 'Approve'}
            </button>
            <button className="danger" disabled={busy} onClick={() => act(() => api.reject(issue.issue_id, note || 'Not actionable'))}>
              Reject
            </button>
          </div>
        </div>
      ) : (
        <div className="row">
          {issue.assigned_crew_name && <span>Assigned to {issue.assigned_crew_name}.</span>}
          {NEXT_STATUS[issue.status] && (
            <button className="secondary" disabled={busy} onClick={() => act(() => api.setStatus(issue.issue_id, NEXT_STATUS[issue.status]))}>
              Mark {NEXT_STATUS[issue.status].replace('_', ' ')}
            </button>
          )}
        </div>
      )}
      {error && <div className="banner error">{error}</div>}

      <h3>Reports ({issue.reports?.length ?? 0})</h3>
      <ul className="reports">
        {issue.reports?.map((r) => (
          <li key={r.report_id}>
            <span className="muted">{new Date(r.created_at).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span> “{r.raw_text}”
            {r.photo_url && (
              <a href={r.photo_url} target="_blank" rel="noreferrer">
                {' '}
                photo
              </a>
            )}
          </li>
        ))}
      </ul>

      <TracePanel events={issue.agent_trace || []} title="Audit trail" emptyText="No agent activity recorded." />
    </section>
  )
}
