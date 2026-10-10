import { useCallback, useEffect, useRef, useState } from 'react'
import { api, subscribe } from '../api.js'
import ChatPanel from './ChatPanel.jsx'
import IssueDetail from './IssueDetail.jsx'
import IssueMap from './IssueMap.jsx'
import IssueQueue from './IssueQueue.jsx'
import StatsBar from './StatsBar.jsx'
import TracePanel from './TracePanel.jsx'

const MAX_EVENTS = 400
const CLOSED = new Set(['resolved', 'rejected'])

function sortIssues(list) {
  return [...list].sort((a, b) => (b.priority_score ?? -1) - (a.priority_score ?? -1) || b.report_count - a.report_count)
}

export default function DispatcherView({ meta }) {
  const [issues, setIssues] = useState([])
  const [events, setEvents] = useState([])
  const [stats, setStats] = useState(null)
  const [selectedId, setSelectedId] = useState(null)
  const [flashIds, setFlashIds] = useState(new Set())
  const [stream, setStream] = useState('connecting')
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const statsTimer = useRef(null)

  const refreshStats = useCallback(() => {
    clearTimeout(statsTimer.current)
    statsTimer.current = setTimeout(() => api.stats().then(setStats).catch(() => {}), 300)
  }, [])

  const reload = useCallback(async () => {
    const [list, s] = await Promise.all([api.issues(), api.stats()])
    setIssues(sortIssues(list))
    setStats(s)
  }, [])

  useEffect(() => {
    reload().catch((e) => setError(e.message))
    return subscribe({
      onStatus: setStream,
      onTrace: (e) => setEvents((prev) => [...prev, e].slice(-MAX_EVENTS)),
      onIssue: (issue) => {
        setIssues((prev) => {
          const rest = prev.filter((i) => i.issue_id !== issue.issue_id)
          return sortIssues(CLOSED.has(issue.status) ? rest : [...rest, issue])
        })
        setFlashIds((prev) => new Set(prev).add(issue.issue_id))
        setTimeout(
          () =>
            setFlashIds((prev) => {
              const next = new Set(prev)
              next.delete(issue.issue_id)
              return next
            }),
          2000,
        )
        refreshStats()
      },
    })
  }, [reload, refreshStats])

  async function runBatch() {
    setBusy('batch')
    setError(null)
    try {
      await api.runDemoBatch()
      await reload()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(null)
    }
  }

  async function resetDemo() {
    if (!window.confirm('Reset all issues to the seeded history?')) return
    setBusy('reset')
    try {
      await api.resetDemo()
      setSelectedId(null)
      setEvents([])
      await reload()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(null)
    }
  }

  const selected = issues.find((i) => i.issue_id === selectedId)
  return (
    <main className="dispatch">
      <StatsBar stats={stats} stream={stream}>
        <button className="primary" onClick={runBatch} disabled={!!busy}>
          {busy === 'batch' ? 'Agents triaging…' : `Run demo batch (${meta.demo_report_count} reports)`}
        </button>
        <button className="secondary" onClick={resetDemo} disabled={!!busy}>
          Reset demo
        </button>
      </StatsBar>
      {error && <div className="banner error">{error}</div>}

      <div className="dispatch-grid">
        <div className="col-map">
          <IssueMap center={meta.center} issues={issues} onSelect={setSelectedId} selectedId={selectedId} flyTo={selected} zoom={12} className="map-large" />
        </div>
        <div className="col-queue">
          {selectedId ? (
            <IssueDetail issueId={selectedId} meta={meta} onClose={() => setSelectedId(null)} liveIssue={selected} />
          ) : (
            <IssueQueue issues={issues} onSelect={setSelectedId} flashIds={flashIds} />
          )}
        </div>
        <div className="col-side">
          <TracePanel events={events} title="Live agent trace" />
          <ChatPanel />
        </div>
      </div>
    </main>
  )
}
