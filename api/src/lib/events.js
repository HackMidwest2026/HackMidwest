// Trace event bus. Every agent step publishes here; the SSE endpoint fans events out to
// dashboards, and the pipeline appends them to the issue's agent_trace for the audit trail.
import { EventEmitter } from 'node:events'
import { randomUUID } from 'node:crypto'

const bus = new EventEmitter()
bus.setMaxListeners(100)

/**
 * Trace event contract (shared with the web app):
 * {
 *   event_id, ts, run_id, report_id?, issue_id?,
 *   agent: 'pipeline' | 'intake' | 'dedup' | 'priority' | 'router' | 'supervisor' | 'dispatcher',
 *   status: 'started' | 'tool' | 'completed' | 'error',
 *   message: human-readable one-liner for the trace panel,
 *   data?: structured output or tool result,
 *   engine?: 'mock' | 'bedrock' | 'fallback', model?, duration_ms?
 * }
 */
export function emitTrace(event) {
  const full = { event_id: randomUUID(), ts: new Date().toISOString(), ...event }
  bus.emit('trace', full)
  return full
}

export function emitIssueUpdate(issue) {
  bus.emit('issue', issue)
}

export function onTrace(fn) {
  bus.on('trace', fn)
  return () => bus.off('trace', fn)
}

export function onIssue(fn) {
  bus.on('issue', fn)
  return () => bus.off('issue', fn)
}
