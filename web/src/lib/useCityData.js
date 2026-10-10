// Shared live state: issues, stats, crews and the agent trace, kept fresh by the SSE stream.
import { useCallback, useEffect, useRef, useState } from 'react'
import { api, subscribe } from '../api.js'

const MAX_EVENTS = 500

function sortIssues(list) {
  return [...list].sort((a, b) => (b.priority_score ?? -1) - (a.priority_score ?? -1) || b.report_count - a.report_count)
}

export function useCityData({ onPipelineEvent } = {}) {
  const [issues, setIssues] = useState([])
  const [stats, setStats] = useState(null)
  const [crews, setCrews] = useState([])
  const [events, setEvents] = useState([])
  const [stream, setStream] = useState('connecting')
  const [flashIds, setFlashIds] = useState(() => new Set())
  const [error, setError] = useState(null)
  const refreshTimer = useRef(null)
  const onPipeline = useRef(onPipelineEvent)
  onPipeline.current = onPipelineEvent

  const refreshSide = useCallback(() => {
    clearTimeout(refreshTimer.current)
    refreshTimer.current = setTimeout(() => {
      api.stats().then(setStats).catch(() => {})
      api.crews().then(setCrews).catch(() => {})
    }, 300)
  }, [])

  const reload = useCallback(async () => {
    try {
      const [list, s, c] = await Promise.all([api.issues('all'), api.stats(), api.crews()])
      setIssues(sortIssues(list))
      setStats(s)
      setCrews(c)
      setError(null)
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => {
    reload()
    return subscribe({
      onStatus: setStream,
      onTrace: (e) => {
        setEvents((prev) => [...prev, e].slice(-MAX_EVENTS))
        if (e.agent === 'pipeline' && e.status === 'completed') onPipeline.current?.(e)
      },
      onIssue: (issue) => {
        setIssues((prev) => sortIssues([...prev.filter((i) => i.issue_id !== issue.issue_id), issue]))
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
        refreshSide()
      },
    })
  }, [reload, refreshSide])

  const replaceIssue = useCallback(
    (issue) => {
      setIssues((prev) => sortIssues([...prev.filter((i) => i.issue_id !== issue.issue_id), { ...prev.find((i) => i.issue_id === issue.issue_id), ...issue }]))
      refreshSide()
    },
    [refreshSide],
  )

  return { issues, stats, crews, events, stream, flashIds, error, reload, replaceIssue, clearEvents: () => setEvents([]) }
}
