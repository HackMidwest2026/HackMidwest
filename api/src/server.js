import express from 'express'
import { randomUUID } from 'node:crypto'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { askSupervisor } from './agents/supervisor.js'
import { departmentName } from './agents/rules.js'
import { config } from './config.js'
import { categories, city, demoReports, departments, seedReports } from './lib/data.js'
import { emitIssueUpdate, emitTrace, onIssue, onTrace } from './lib/events.js'
import { geocodeAddress, reverseGeocode } from './lib/geo.js'
import * as store from './lib/store.js'
import { processBatch, processReport, seedHistory } from './pipeline.js'
import { findNearbyIssues, getStats } from './tools/cityTools.js'

const app = express()
app.use(express.json({ limit: '10mb' }))

const uploadsDir = join(config.stateDir, 'uploads')
mkdirSync(uploadsDir, { recursive: true })
app.use('/uploads', express.static(uploadsDir, { maxAge: '1h' }))

const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next)

const STATUS_FLOW = ['new', 'triaged', 'approved', 'assigned', 'in_progress', 'resolved', 'rejected']

function issueView(issue, { withReports = false } = {}) {
  if (!issue) return null
  const crew = issue.recommended_crew ? store.getCrew(issue.recommended_crew) : null
  const assigned = issue.assigned_crew ? store.getCrew(issue.assigned_crew) : null
  return {
    ...issue,
    recommended_department_name: issue.recommended_department ? departmentName(issue.recommended_department) : null,
    recommended_crew_name: crew?.name ?? null,
    assigned_crew_name: assigned?.name ?? null,
    ...(withReports ? { reports: store.reportsForIssue(issue.issue_id) } : { agent_trace: undefined }),
  }
}

function savePhoto(dataUrl) {
  const m = /^data:image\/(png|jpe?g|webp|gif);base64,(.+)$/.exec(dataUrl || '')
  if (!m) return null
  const ext = m[1] === 'jpeg' ? 'jpg' : m[1]
  const name = `${randomUUID()}.${ext}`
  writeFileSync(join(uploadsDir, name), Buffer.from(m[2], 'base64'))
  return `/uploads/${name}`
}

// ---------- meta ----------

app.get('/api/health', (_req, res) => res.json({ ok: true, mode: config.mode, models: config.mode === 'bedrock' ? config.models : null }))

app.get('/api/meta', (_req, res) =>
  res.json({
    mode: config.mode,
    center: city.center,
    neighborhoods: city.neighborhoods,
    sensitive_sites: city.sensitive_sites,
    categories: categories.map(({ id, name, department_id, subcategories }) => ({ id, name, department_id, subcategories: subcategories.map(({ id, name }) => ({ id, name })) })),
    departments,
    crews: store.listCrews(),
    statuses: STATUS_FLOW,
    demo_report_count: demoReports.length,
  }),
)

// Open issues near a point, for the "matching nearby reports" hint before a resident submits.
app.get('/api/nearby', (req, res) => {
  const lat = Number(req.query.lat)
  const lng = Number(req.query.lng)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return res.status(400).json({ error: 'lat and lng are required' })
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

app.get('/api/geocode', (req, res) => res.json(geocodeAddress(String(req.query.q || ''))))
app.get('/api/reverse-geocode', (req, res) => res.json(reverseGeocode({ lat: Number(req.query.lat), lng: Number(req.query.lng) })))

// ---------- reports ----------

app.post(
  '/api/reports',
  wrap(async (req, res) => {
    const { text, lat, lng, address, photo, reporter_contact, client_run_id, category_hint } = req.body || {}
    if (!text || !String(text).trim()) return res.status(400).json({ error: 'Describe the problem in a few words.' })
    const photo_url = photo ? savePhoto(photo) : null
    // client_run_id lets the resident page pick its own run out of the live trace stream.
    const runId = /^[\w-]{8,64}$/.test(client_run_id || '') ? client_run_id : randomUUID()
    const result = await processReport({ raw_text: String(text).trim(), lat, lng, address, photo_url, reporter_contact, category_hint }, { runId })
    res.status(201).json({ ...result, issue: issueView(result.issue, { withReports: true }) })
  }),
)

app.get('/api/reports', (_req, res) => res.json(store.listReports().slice(-200).reverse()))

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

app.get('/api/issues/:id', (req, res) => {
  const issue = store.getIssue(req.params.id)
  if (!issue) return res.status(404).json({ error: 'Issue not found' })
  res.json(issueView(issue, { withReports: true }))
})

function dispatcherAction(issue, status, extra, message) {
  const now = new Date().toISOString()
  const updated = store.updateIssue(issue.issue_id, {
    status,
    ...extra,
    status_history: [...issue.status_history, { status, at: now, by: 'dispatcher', ...(extra.dispatcher_note && { note: extra.dispatcher_note }) }],
  })
  const evt = emitTrace({ run_id: randomUUID(), issue_id: issue.issue_id, agent: 'dispatcher', status: 'completed', message })
  store.updateIssue(issue.issue_id, { agent_trace: [...updated.agent_trace, evt] })
  emitIssueUpdate(updated)
  return updated
}

app.post('/api/issues/:id/approve', (req, res) => {
  const issue = store.getIssue(req.params.id)
  if (!issue) return res.status(404).json({ error: 'Issue not found' })
  const { crew_id, department_id, note } = req.body || {}
  const crewId = crew_id || issue.recommended_crew
  const crew = crewId ? store.getCrew(crewId) : null
  if (crewId && !crew) return res.status(400).json({ error: `Unknown crew ${crewId}` })
  if (crew && issue.assigned_crew !== crew.crew_id) {
    crew.open_jobs += 1
    const prev = issue.assigned_crew && store.getCrew(issue.assigned_crew)
    if (prev) prev.open_jobs = Math.max(0, prev.open_jobs - 1)
  }
  const edited = (crew_id && crew_id !== issue.recommended_crew) || (department_id && department_id !== issue.recommended_department)
  const updated = dispatcherAction(
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

app.post('/api/issues/:id/reject', (req, res) => {
  const issue = store.getIssue(req.params.id)
  if (!issue) return res.status(404).json({ error: 'Issue not found' })
  const note = req.body?.reason || 'Rejected by dispatcher'
  res.json(issueView(dispatcherAction(issue, 'rejected', { dispatcher_note: note }, `Dispatcher rejected #${issue.issue_id}: ${note}`)))
})

app.patch('/api/issues/:id', (req, res) => {
  const issue = store.getIssue(req.params.id)
  if (!issue) return res.status(404).json({ error: 'Issue not found' })
  const { status } = req.body || {}
  if (!STATUS_FLOW.includes(status)) return res.status(400).json({ error: `status must be one of ${STATUS_FLOW.join(', ')}` })
  if (['resolved', 'rejected'].includes(status) && issue.assigned_crew) {
    const crew = store.getCrew(issue.assigned_crew)
    if (crew) crew.open_jobs = Math.max(0, crew.open_jobs - 1)
  }
  res.json(issueView(dispatcherAction(issue, status, {}, `Dispatcher moved #${issue.issue_id} to ${status.replace('_', ' ')}.`)))
})

app.get('/api/stats', (_req, res) => res.json({ ...getStats(), last_batch: store.getLastBatch() }))

// ---------- supervisor chat ----------

app.post(
  '/api/chat',
  wrap(async (req, res) => {
    const question = String(req.body?.question || '').trim()
    if (!question) return res.status(400).json({ error: 'Ask a question.' })
    const runId = /^[\w-]{8,64}$/.test(req.body?.client_run_id || '') ? req.body.client_run_id : randomUUID()
    const answer = await askSupervisor(question, { trace: (e) => emitTrace({ run_id: runId, ...e }) })
    res.json({ answer, run_id: runId })
  }),
)

// ---------- demo controls ----------

let batchRunning = false
app.post(
  '/api/demo/batch',
  wrap(async (req, res) => {
    if (batchRunning) return res.status(409).json({ error: 'A batch is already running.' })
    batchRunning = true
    try {
      const count = Math.min(Number(req.body?.count) || demoReports.length, demoReports.length)
      const metrics = await processBatch(demoReports.slice(0, count), { label: 'Demo batch' })
      store.setLastBatch(metrics)
      res.json(metrics)
    } finally {
      batchRunning = false
    }
  }),
)

app.post(
  '/api/demo/reset',
  wrap(async (_req, res) => {
    store.resetState()
    const metrics = await seedHistory(seedReports)
    store.setLastBatch(null)
    emitTrace({ run_id: randomUUID(), agent: 'pipeline', status: 'completed', message: 'Demo reset: history re-seeded.' })
    res.json({ ok: true, seeded: metrics })
  }),
)

// ---------- live trace stream (SSE) ----------

app.get('/api/stream', (req, res) => {
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    Connection: 'keep-alive',
    'X-Accel-Buffering': 'no',
  })
  res.write(`event: hello\ndata: ${JSON.stringify({ mode: config.mode })}\n\n`)
  const send = (type) => (data) => res.write(`event: ${type}\ndata: ${JSON.stringify(type === 'issue' ? issueView(data) : data)}\n\n`)
  const offTrace = onTrace(send('trace'))
  const offIssue = onIssue(send('issue'))
  const ping = setInterval(() => res.write(': ping\n\n'), 20000)
  req.on('close', () => {
    clearInterval(ping)
    offTrace()
    offIssue()
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
  if (!store.loadState()) {
    const m = await seedHistory(seedReports)
    console.log(`Seeded ${m.reports} historical reports into ${m.issues} issues.`)
  }
  const shutdown = () => {
    store.saveNow()
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
  return app.listen(config.port, () => console.log(`CityCare API on :${config.port} (mode=${config.mode}, data=${config.dataDir}, state=${config.stateDir})`))
}

export { app }

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) start()
