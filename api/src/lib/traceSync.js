// Live agent trace across API instances that share one MongoDB database (teammates each
// running the app against the same Atlas cluster).
//
// Trace events (every agent step and tool call) are emitted in the process that ran the
// agents, so on their own they reach only that instance's browsers. Here each instance:
//   - writes its own events to the trace_events collection in small batches, and
//   - polls for the other instances' events and replays them on its local event bus, so the
//     Live Agent Trace, the dedup log and the "new incident" toasts show everyone's activity.
// Issues and reports themselves are synced separately (store.startSync).
import { randomUUID } from 'node:crypto'
import { emitTraceAsIs, onTrace } from './events.js'
import * as store from './store.js'

const FLUSH_MS = 500
const OVERLAP_MS = 10000 // re-read a little history to cover clock skew and late writes
const MAX_DATA_CHARS = 4000 // big tool outputs (query results) stay local; the message still syncs
const SEEN_LIMIT = 5000

/** This process, as the other instances see it. */
export const INSTANCE_ID = randomUUID()

function slim(event) {
  if (event.data === undefined) return event
  return JSON.stringify(event.data).length > MAX_DATA_CHARS ? { ...event, data: undefined } : event
}

/** Start sharing. Returns a stop function, or null when the backend can't share (file storage). */
export function startTraceSync({ pollMs = 1000, log = console } = {}) {
  if (!store.canShareTrace() || !(pollMs > 0)) return null

  // ---- outgoing ----
  let outbox = []
  const offTrace = onTrace((event) => {
    if (!event.instance) outbox.push(slim(event)) // events replayed from others carry `instance`
  })
  let lastWriteError = null
  const flush = async () => {
    if (!outbox.length) return
    const batch = outbox
    outbox = []
    try {
      await store.saveTraceEvents(INSTANCE_ID, batch)
      lastWriteError = null
    } catch (err) {
      // Live trace is best effort: drop the batch rather than pile up while the database is away.
      if (err.message !== lastWriteError) log.warn(`[trace] could not share ${batch.length} trace event(s): ${err.message}`)
      lastWriteError = err.message
    }
  }
  const flushTimer = setInterval(flush, FLUSH_MS)
  flushTimer.unref?.()

  // ---- incoming ----
  let cursor = Date.now()
  const seen = new Set()
  let polling = false
  let lastReadError = null
  const poll = async () => {
    if (polling) return
    polling = true
    try {
      const events = await store.traceEventsSince(new Date(cursor - OVERLAP_MS), INSTANCE_ID)
      for (const e of events) {
        const t = new Date(e.ts).getTime()
        if (t > cursor) cursor = t
        if (seen.has(e.event_id)) continue
        seen.add(e.event_id)
        emitTraceAsIs(e)
      }
      if (seen.size > SEEN_LIMIT) {
        const keep = [...seen].slice(-SEEN_LIMIT / 2)
        seen.clear()
        keep.forEach((id) => seen.add(id))
      }
      lastReadError = null
    } catch (err) {
      if (err.message !== lastReadError) log.warn(`[trace] could not read other instances' trace events: ${err.message}`)
      lastReadError = err.message
    } finally {
      polling = false
    }
  }
  const pollTimer = setInterval(poll, pollMs)
  pollTimer.unref?.()

  return async function stop() {
    clearInterval(flushTimer)
    clearInterval(pollTimer)
    offTrace()
    await flush()
  }
}
