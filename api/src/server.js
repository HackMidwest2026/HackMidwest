import express from 'express'
import { randomUUID } from 'node:crypto'
import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { planRoutes } from './agents/routes.js'
import { askSupervisor } from './agents/supervisor.js'
import { departmentName } from './agents/rules.js'
import { config } from './config.js'
import { categories, city, cityProfile, departments, seedReports } from './lib/data.js'
import { emitIssueUpdate, emitReload, emitTrace, onIssue, onReload, onTrace } from './lib/events.js'
import { describePoint, locateText, suggest } from './lib/locate.js'
import { authRoutes, currentUser, requireDispatcher } from './lib/auth.js'
import * as store from './lib/store.js'
import { startTraceSync } from './lib/traceSync.js'
import { bedrockLimiter } from './agents/llm.js'
import { GRAPH_TOPOLOGY, processBatch, processReport, reportQueue, seedHistory } from './pipeline.js'
import { findNearbyIssues, getStats } from './tools/cityTools.js'

const app = express()
// Behind nginx or the Vite dev proxy on a private network: use X-Forwarded-For for the client address.
app.set('trust proxy', 'loopback, linklocal, uniquelocal')
app.use(express.json({ limit: '25mb' })) // room for an unconverted phone photo

const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next)

// Dispatcher accounts (sign up, log in, log out). Dispatcher-only routes below use requireDispatcher.
authRoutes(app, wrap)

// Report photos live in the store (MongoDB in production, files offline), so any API
// instance can serve them. Names are random UUIDs, so they can be cached for a long time.
app.get(
  '/uploads/:name',
  wrap(async (req, res) => {
    if (!/^[\w-]+\.(png|jpg|jpeg|webp|gif)$/.test(req.params.name)) return res.status(404).end()
    const photo = await store.readPhoto(req.params.name)
    if (!photo) return res.status(404).end()
    res.set({ 'Content-Type': photo.mime, 'Cache-Control': 'public, max-age=86400, immutable' }).send(photo.bytes)
  }),
)

const STATUS_FLOW = ['new', 'triaged', 'approved', 'assigned', 'in_progress', 'resolved', 'rejected']

// Residents' contact details are for dispatchers only: any view that includes reports leaves
// them out unless the caller is a signed-in dispatcher (contacts: true).
const withoutContact = ({ reporter_contact: _c, ...report }) => report

function issueView(issue, { withReports = false, contacts = false } = {}) {
  if (!issue) return null
  const crew = issue.recommended_crew ? store.getCrew(issue.recommended_crew) : null
  const assigned = issue.assigned_crew ? store.getCrew(issue.assigned_crew) : null
  return {
    ...issue,
    recommended_department_name: issue.recommended_department ? departmentName(issue.recommended_department) : null,
    recommended_crew_name: crew?.name ?? null,
    assigned_crew_name: assigned?.name ?? null,
    ...(withReports ? { reports: store.reportsForIssue(issue.issue_id).map((r) => (contacts ? r : withoutContact(r))) } : { agent_trace: undefined }),
  }
}


/**
 * Validate a coordinate pair from a request. Returns { lat, lng } as numbers, null when both
 * are missing (the caller may locate the report from its text), or { error } when they are
 * not numbers on Earth.
 */
function readPoint(lat, lng, { required = false } = {}) {
  const blank = (v) => v === undefined || v === null || v === ''
  if (blank(lat) && blank(lng)) return required ? { error: 'lat and lng are required' } : null
  const point = { lat: Number(lat), lng: Number(lng) }
  if (blank(lat) || blank(lng) || !Number.isFinite(point.lat) || !Number.isFinite(point.lng)) return { error: 'lat and lng must both be numbers.' }
  if (Math.abs(point.lat) > 90 || Math.abs(point.lng) > 180) return { error: 'lat must be between -90 and 90 and lng between -180 and 180.' }
  return point
}

// ---------- meta ----------

app.get('/api/health', (_req, res) =>
  res.json({
    ok: true,
    mode: config.mode,
    models: config.mode === 'bedrock' ? config.models : null,
    database: store.storeInfo(),
    ...(config.mode === 'bedrock' && { report_queue: reportQueue.stats(), bedrock_calls: bedrockLimiter.stats() }),
  }),
)

app.get('/api/graph', (_req, res) => res.json(GRAPH_TOPOLOGY))

app.get('/api/meta', (_req, res) =>
  res.json({
    mode: config.mode,
    city: { name: cityProfile.name, region: cityProfile.region, default_zoom: cityProfile.default_zoom, examples: cityProfile.examples },
    center: city.center,
    neighborhoods: city.neighborhoods,
    sensitive_sites: city.sensitive_sites,
    categories: categories.map(({ id, name, department_id, subcategories }) => ({ id, name, department_id, subcategories: subcategories.map(({ id, name }) => ({ id, name })) })),
    departments,
    crews: store.listCrews(),
    statuses: STATUS_FLOW,
  }),
)

// Open issues near a point, for the "matching nearby reports" hint before a resident submits.
app.get('/api/nearby', (req, res) => {
  const point = readPoint(req.query.lat, req.query.lng, { required: true })
  if (point.error) return res.status(400).json({ error: point.error })
  const { lat, lng } = point
  const radius = Math.min(Number(req.query.radius) || 120, 500)
  res.json(findNearbyIssues({ lat, lng, radius_m: radius, category: req.query.category || undefined, text: req.query.text || '' }))
})

app.get('/api/crews', (_req, res) => {
  const open = store.listIssues().filter((i) => ['approved', 'assigned', 'in_progress'].includes(i.status))
  res.json(
    store.listCrews().map((c) => ({
      ...c,
      department_name: departmentName(c.department_id),
      active_issue_ids: open.filter((i) => i.assigned_crew === c.crew_id).map((i) => i.issue_id),
    })),
  )
})

// Location lookups work for any place: local city data first, then OpenStreetMap (Photon).
// lat/lng (the user's current map view) bias results toward where they are looking.
const biasFrom = (q) => (Number.isFinite(Number(q.lat)) && Number.isFinite(Number(q.lng)) ? { lat: Number(q.lat), lng: Number(q.lng) } : undefined)

app.get(
  '/api/address-suggest',
  wrap(async (req, res) => {
    const q = String(req.query.q || '').trim().slice(0, 120)
    res.json(q.length < 2 ? [] : await suggest(q, biasFrom(req.query)))
  }),
)

app.get(
  '/api/geocode',
  wrap(async (req, res) => {
    const found = await locateText(String(req.query.q || ''), biasFrom(req.query))
    res.json(found ? { found: true, ...found } : { found: false, reason: 'Could not find that place. Try a full street address or drop a pin.' })
  }),
)

app.get(
  '/api/reverse-geocode',
  wrap(async (req, res) => {
    const point = readPoint(req.query.lat, req.query.lng, { required: true })
    if (point.error) return res.status(400).json({ error: point.error })
    res.json(await describePoint(point))
  }),
)

// ---------- reports ----------

app.post(
  '/api/reports',
  wrap(async (req, res) => {
    const { text, address, photo, reporter_contact, client_run_id, category_hint } = req.body || {}
    const point = readPoint(req.body?.lat, req.body?.lng)
    if (point?.error) return res.status(400).json({ error: point.error })
    const { lat, lng } = point || {}
    // Any common image format; stored as an upright, resized JPEG without location metadata.
    // An unusable file throws a 400 with a message for the resident.
    const photo_url = photo ? await store.savePhoto(photo) : null
    // A photo can stand in for the description; the Vision agent reads it in Bedrock mode.
    if (!String(text || '').trim() && !photo_url) return res.status(400).json({ error: 'Describe the problem in a few words or attach a photo.' })
    // client_run_id lets the resident page pick its own run out of the live trace stream.
    const runId = /^[\w-]{8,64}$/.test(client_run_id || '') ? client_run_id : randomUUID()
    const result = await processReport(
      { raw_text: String(text || '').trim() || '(photo only, no description)', lat, lng, address, photo_url, reporter_contact, category_hint },
      { runId },
    )
    // The issue may hold other residents' reports: their contact details stay out (issueView).
    res.status(201).json({ ...result, issue: issueView(result.issue, { withReports: true }) })
  }),
)

app.get('/api/reports', requireDispatcher, (_req, res) => res.json(store.listReports().slice(-200).reverse()))

// ---------- issues ----------

app.get('/api/issues', (req, res) => {
  const { status = 'open', neighborhood, category } = req.query
  const issues = store
    .listIssues()
    .filter((i) => (status === 'open' ? !['resolved', 'rejected'].includes(i.status) : status === 'all' || i.status === status))
    .filter((i) => !neighborhood || i.neighborhood === neighborhood)
    .filter((i) => !category || i.category === category)
    .sort((a, b) => (b.priority_score ?? -1) - (a.priority_score ?? -1) || b.report_count - a.report_count)
  res.json(issues.map((i) => issueView(i)))
})

app.get(
  '/api/issues/:id',
  wrap(async (req, res) => {
    const issue = store.getIssue(req.params.id)
    if (!issue) return res.status(404).json({ error: 'Issue not found' })
    res.json(issueView(issue, { withReports: true, contacts: Boolean(await currentUser(req)) }))
  }),
)

function dispatcherAction(req, issue, status, extra, message) {
  const now = new Date().toISOString()
  const updated = store.updateIssue(issue.issue_id, {
    status,
    ...extra,
    status_history: [...issue.status_history, { status, at: now, by: req.dispatcher?.name || 'dispatcher', ...(extra.dispatcher_note && { note: extra.dispatcher_note }) }],
  })
  const by = req.dispatcher?.name ? ` (${req.dispatcher.name})` : ''
  const evt = emitTrace({ run_id: randomUUID(), issue_id: issue.issue_id, agent: 'dispatcher', status: 'completed', message: `${message}${by}` })
  store.updateIssue(issue.issue_id, { agent_trace: [...updated.agent_trace, evt] })
  emitIssueUpdate(updated)
  return updated
}

app.post('/api/issues/:id/approve', requireDispatcher, (req, res) => {
  const issue = store.getIssue(req.params.id)
  if (!issue) return res.status(404).json({ error: 'Issue not found' })
  const { crew_id, department_id, note } = req.body || {}
  const crewId = crew_id || issue.recommended_crew
  const crew = crewId ? store.getCrew(crewId) : null
  if (crewId && !crew) return res.status(400).json({ error: `Unknown crew ${crewId}` })
  // Approving reopens a closed issue; a closed issue's crew was already credited when it closed.
  const wasOpen = !CLOSED.has(issue.status)
  if (crew && (issue.assigned_crew !== crew.crew_id || !wasOpen)) {
    store.updateCrew(crew.crew_id, (c) => ({ open_jobs: c.open_jobs + 1 }))
    if (issue.assigned_crew && wasOpen && issue.assigned_crew !== crew.crew_id) store.updateCrew(issue.assigned_crew, (c) => ({ open_jobs: Math.max(0, c.open_jobs - 1) }))
  }
  const edited = (crew_id && crew_id !== issue.recommended_crew) || (department_id && department_id !== issue.recommended_department)
  const updated = dispatcherAction(
    req,
    issue,
    crew ? 'assigned' : 'approved',
    {
      assigned_crew: crew?.crew_id ?? null,
      recommended_department: department_id || crew?.department_id || issue.recommended_department,
      dispatcher_note: note || null,
    },
    `Dispatcher ${edited ? 'edited and approved' : 'approved'} #${issue.issue_id}${crew ? `: assigned to ${crew.name}` : ''}.`,
  )
  res.json(issueView(updated))
})

// A crew's open_jobs counts its open assignments (on top of its simulated baseline). Adjust it
// only when an issue actually moves between open and closed, so repeating a status change
// (resolving twice) can't drift the count.
const CLOSED = new Set(['resolved', 'rejected'])
function adjustCrewJobs(issue, nextStatus) {
  if (!issue.assigned_crew) return
  const delta = !CLOSED.has(issue.status) && CLOSED.has(nextStatus) ? -1 : CLOSED.has(issue.status) && !CLOSED.has(nextStatus) ? 1 : 0
  if (delta) store.updateCrew(issue.assigned_crew, (c) => ({ open_jobs: Math.max(0, c.open_jobs + delta) }))
}

app.post('/api/issues/:id/reject', requireDispatcher, (req, res) => {
  const issue = store.getIssue(req.params.id)
  if (!issue) return res.status(404).json({ error: 'Issue not found' })
  const note = req.body?.reason || 'Rejected by dispatcher'
  adjustCrewJobs(issue, 'rejected')
  res.json(issueView(dispatcherAction(req, issue, 'rejected', { dispatcher_note: note }, `Dispatcher rejected #${issue.issue_id}: ${note}`)))
})

app.patch('/api/issues/:id', requireDispatcher, (req, res) => {
  const issue = store.getIssue(req.params.id)
  if (!issue) return res.status(404).json({ error: 'Issue not found' })
  const { status } = req.body || {}
  if (!STATUS_FLOW.includes(status)) return res.status(400).json({ error: `status must be one of ${STATUS_FLOW.join(', ')}` })
  adjustCrewJobs(issue, status)
  res.json(issueView(dispatcherAction(req, issue, status, {}, `Dispatcher moved #${issue.issue_id} to ${status.replace('_', ' ')}.`)))
})

app.get('/api/stats', (_req, res) => res.json({ ...getStats(), last_batch: store.getLastBatch() }))

// ---------- supervisor chat ----------

app.post(
  '/api/chat',
  requireDispatcher,
  wrap(async (req, res) => {
    const question = String(req.body?.question || '').trim()
    if (!question) return res.status(400).json({ error: 'Ask a question.' })
    const runId = /^[\w-]{8,64}$/.test(req.body?.client_run_id || '') ? req.body.client_run_id : randomUUID()
    const answer = await askSupervisor(question, { trace: (e) => emitTrace({ run_id: runId, ...e }) })
    res.json({ answer, run_id: runId })
  }),
)

// Route Planner agent: group each crew's open jobs into trips for today's shift.
app.get('/api/routes', requireDispatcher, (_req, res) => res.json(store.getLastRoutePlan()))

app.post(
  '/api/routes/plan',
  requireDispatcher,
  wrap(async (req, res) => {
    const runId = /^[\w-]{8,64}$/.test(req.body?.client_run_id || '') ? req.body.client_run_id : randomUUID()
    const plan = await planRoutes({ runId })
    store.setLastRoutePlan(plan)
    res.json(plan)
  }),
)

// ---------- reset ----------

// Delete every incident and report (accounts are kept). With SEED_SOURCE=sample, the bundled
// sample reports are loaded again; otherwise the app starts empty and fills up as residents
// submit reports.
app.post(
  '/api/reset',
  requireDispatcher,
  wrap(async (_req, res) => {
    await store.resetState()
    const seeded = config.seedSample ? await seedHistory(seedReports) : null
    store.setLastBatch(null)
    emitTrace({ run_id: randomUUID(), agent: 'pipeline', status: 'completed', message: seeded ? `Reset: loaded ${seeded.reports} sample reports.` : 'Reset: all reports and incidents deleted.' })
    emitReload('reset')
    res.json({ ok: true, seeded, source: seeded ? 'sample' : 'empty' })
  }),
)

// ---------- live trace stream (SSE) ----------

// One listener per event type, fanned out to every connected browser (rather than three
// listeners per connection, which hit Node's listener limit past ~100 open streams). Each
// event is serialized once, however many browsers are watching.
const streamClients = new Set()
function broadcast(type, data) {
  if (!streamClients.size) return
  const chunk = `event: ${type}\ndata: ${JSON.stringify(data)}\n\n`
  for (const res of streamClients) res.write(chunk)
}
onTrace((e) => broadcast('trace', e))
onIssue((issue) => broadcast('issue', issueView(issue)))
onReload((e) => broadcast('reload', e))

app.get('/api/stream', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no',
  })
  res.write(`event: hello\ndata: ${JSON.stringify({ mode: config.mode })}\n\n`)
  streamClients.add(res)
  const ping = setInterval(() => res.write(': ping\n\n'), 20000)
  req.on('close', () => {
    clearInterval(ping)
    streamClients.delete(res)
  })
})

// ---------- optional: serve the built web app from this process ----------

if (process.env.STATIC_DIR && existsSync(process.env.STATIC_DIR)) {
  app.use(express.static(process.env.STATIC_DIR))
  app.get(/^\/(?!api|uploads).*/, (_req, res) => res.sendFile(join(process.env.STATIC_DIR, 'index.html')))
}

app.use((err, _req, res, _next) => {
  const status = err.status || 500
  if (status >= 500) console.error(err)
  res.status(status).json({ error: err.message || 'Internal error' })
})

// ---------- startup ----------

export async function start() {
  try {
    if (!(await store.initStore())) {
      if (config.seedSample) {
        const m = await seedHistory(seedReports)
        await store.flush()
        console.log(`Seeded ${m.reports} sample reports into ${m.issues} issues (SEED_SOURCE=sample).`)
      } else {
        console.log('No reports yet: incidents appear as residents submit them on the website.')
      }
    }
  } catch (err) {
    console.error(`Could not open the ${process.env.DATABASE_URL ? 'MongoDB database (check DATABASE_URL and the Atlas IP access list)' : 'data store'}: ${err.message}`)
    process.exit(1)
  }
  console.log(`Database: ${store.storeInfo().backend === 'mongodb' ? 'MongoDB (DATABASE_URL)' : `local file in ${config.stateDir}`}`)
  // Other API instances sharing the database: show their changes here too.
  store.onRemoteChange((e) => (e.type === 'reload' ? emitReload('remote') : emitIssueUpdate(e.issue)))
  if (store.startSync(config.syncIntervalMs)) console.log(`Syncing with other instances every ${config.syncIntervalMs / 1000}s.`)
  // ...and their agents' live trace, so the trace and dedup log show everyone's reports.
  const stopTraceSync = startTraceSync({ pollMs: config.traceSyncMs })
  let stopping = false
  const shutdown = async () => {
    if (stopping) return
    stopping = true
    // Write anything still pending before exiting (bounded so a dead database can't hang shutdown).
    const close = async () => {
      await stopTraceSync?.() // share the last trace events
      await store.closeStore()
    }
    await Promise.race([close(), new Promise((r) => setTimeout(r, 5000))])
    process.exit(0)
  }
  process.on('SIGINT', shutdown)
  process.on('SIGTERM', shutdown)
  if (!['mock', 'bedrock'].includes(config.mode)) {
    console.warn(`Unknown mode "${config.mode}" from ${config.modeSource}; expected "mock" or "bedrock". Running the rule-based engine.`)
  }
  console.log(
    config.mode === 'bedrock'
      ? `Engine: Bedrock (from ${config.modeSource}) region=${config.awsRegion} intake=${config.models.intake} reasoning=${config.models.reasoning}`
      : `Engine: mock rule-based agents (${config.modeSource === 'default' ? 'CITYCARE_MODE not set' : `from ${config.modeSource}`}). Set CITYCARE_MODE=bedrock to use Claude on Bedrock.`,
  )
  return app.listen(config.port, () => console.log(`CityCare API on :${config.port} (mode=${config.mode}, data=${config.dataDir}, state=${store.storeInfo().backend === 'file' ? config.stateDir : 'mongodb'})`))
}

export { app }

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) start()
