// The app's data layer. Everything reads and writes state through these functions.
//
// Storage backends:
//   - MongoDB through Prisma when DATABASE_URL is set: the central database. (see lib/mongo.js)
//   - A JSON file under STATE_DIR otherwise: offline demos and tests.
//
// Reads are served from an in-memory working copy (the agents and tools query it many times
// per report, synchronously). Every change marks its record dirty, and dirty records are
// written to the backend shortly after, in order, with retries if the database is
// unreachable. Run one API instance per database: instances don't see each other's writes
// until they restart.
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { readFile, writeFile } from 'node:fs/promises'
import { randomUUID } from 'node:crypto'
import { join } from 'node:path'
import { config } from '../config.js'
import { crewSeed } from './data.js'

const FLUSH_DELAY_MS = 150
const RETRY_DELAY_MS = 5000

function emptyState() {
  return {
    next_issue_id: 1040,
    next_report_id: 1,
    issues: [],
    reports: [],
    crews: structuredClone(crewSeed),
    last_batch: null,
    last_route_plan: null,
  }
}

let state = emptyState()

// ---------- backends ----------

const uploadsDir = () => join(config.stateDir, 'uploads')

function fileBackend() {
  const path = () => join(config.stateDir, 'state.json')
  return {
    name: 'file',
    async connect() {
      mkdirSync(config.stateDir, { recursive: true })
    },
    async load() {
      return existsSync(path()) ? JSON.parse(readFileSync(path(), 'utf8')) : null
    },
    // The file always holds the whole state, so a save rewrites it.
    async save() {
      mkdirSync(config.stateDir, { recursive: true })
      writeFileSync(`${path()}.tmp`, JSON.stringify(state))
      renameSync(`${path()}.tmp`, path())
    },
    async clear() {},
    async savePhoto(name, _mime, bytes) {
      mkdirSync(uploadsDir(), { recursive: true })
      await writeFile(join(uploadsDir(), name), bytes)
    },
    async readPhoto(name) {
      try {
        return { mime: MIME[name.split('.').pop()] || 'application/octet-stream', bytes: await readFile(join(uploadsDir(), name)) }
      } catch {
        return null
      }
    },
    async disconnect() {},
  }
}

let backend = fileBackend()

// ---------- change tracking & write-through ----------

const dirty = { issues: new Set(), reports: new Set(), crews: new Set(), state: new Set() }
let clearPending = false
let flushTimer = null
let chain = Promise.resolve()
let lastError = null
let retryTimer = null
let closing = false

function markDirty(kind, id) {
  dirty[kind].add(id)
  saveSoon()
}

export function saveSoon() {
  if (flushTimer) return
  flushTimer = setTimeout(() => {
    flushTimer = null
    flush().catch(() => {})
  }, FLUSH_DELAY_MS)
}

/** Write all pending changes now. Resolves when they are stored. */
export function flush() {
  chain = chain.then(writePending, writePending)
  return chain
}

async function writePending() {
  const wasClear = clearPending
  const taken = {
    issues: [...dirty.issues],
    reports: [...dirty.reports],
    crews: [...dirty.crews],
    state: [...dirty.state],
  }
  if (!wasClear && Object.values(taken).every((a) => a.length === 0)) return
  for (const s of Object.values(dirty)) s.clear()
  clearPending = false
  // Snapshot so later in-memory edits during the await don't race the write.
  const changes = {
    issues: taken.issues.map(getIssue).filter(Boolean).map((o) => structuredClone(o)),
    reports: taken.reports.map(getReport).filter(Boolean).map((o) => structuredClone(o)),
    crews: taken.crews.map(getCrew).filter(Boolean).map((o) => structuredClone(o)),
    state: Object.fromEntries(taken.state.map((k) => [k, structuredClone(stateValue(k))])),
  }
  try {
    if (wasClear) await backend.clear()
    await backend.save(changes)
    lastError = null
  } catch (err) {
    // Keep the changes and try again: nothing is lost if the database blips.
    lastError = `${err.name}: ${err.message}`
    console.error(`[store] write to ${backend.name} failed, retrying in ${RETRY_DELAY_MS / 1000}s:`, lastError)
    if (wasClear) clearPending = true
    taken.issues.forEach((id) => dirty.issues.add(id))
    taken.reports.forEach((id) => dirty.reports.add(id))
    taken.crews.forEach((id) => dirty.crews.add(id))
    taken.state.forEach((k) => dirty.state.add(k))
    if (!retryTimer && !closing) {
      retryTimer = setTimeout(() => {
        retryTimer = null
        saveSoon()
      }, RETRY_DELAY_MS)
      retryTimer.unref?.()
    }
  }
}

function stateValue(key) {
  if (key === 'counters') return { next_issue_id: state.next_issue_id, next_report_id: state.next_report_id }
  return state[key] ?? null
}

// ---------- lifecycle ----------

/**
 * Pick the backend and load saved data. Returns true if there was data to load.
 * With DATABASE_URL set this connects to MongoDB and throws if it can't.
 */
export async function initStore() {
  if (process.env.DATABASE_URL) {
    const { createMongoBackend } = await import('./mongo.js')
    backend = createMongoBackend(process.env.DATABASE_URL)
  }
  await backend.connect()
  const saved = await backend.load()
  if (!saved) return false
  state = { ...emptyState(), ...saved }
  if (!saved.crews?.length) {
    state.crews = structuredClone(crewSeed)
    state.crews.forEach((c) => dirty.crews.add(c.crew_id))
    saveSoon()
  }
  return true
}

/** Kept for callers that load synchronously (file backend only). */
export function loadState() {
  mkdirSync(config.stateDir, { recursive: true })
  const path = join(config.stateDir, 'state.json')
  if (!existsSync(path)) return false
  state = { ...emptyState(), ...JSON.parse(readFileSync(path, 'utf8')) }
  return true
}

export async function closeStore() {
  clearTimeout(flushTimer)
  flushTimer = null
  await flush()
  closing = true
  clearTimeout(retryTimer)
  retryTimer = null
  if (lastError) console.error(`[store] closing with ${storeInfo().pending_writes} unsaved change(s): ${lastError}`)
  await backend.disconnect()
}

export function storeInfo() {
  return {
    backend: backend.name,
    pending_writes: Object.values(dirty).reduce((n, s) => n + s.size, 0),
    last_error: lastError,
  }
}

/** Wipe all data and start over with the seed crews (demo reset). */
export function resetState() {
  state = emptyState()
  for (const s of Object.values(dirty)) s.clear()
  clearPending = true
  state.crews.forEach((c) => dirty.crews.add(c.crew_id))
  ;['counters', 'last_batch', 'last_route_plan'].forEach((k) => dirty.state.add(k))
  saveSoon()
}

// ---------- reports ----------
export function createReport(fields) {
  const report = {
    report_id: `R-${String(state.next_report_id++).padStart(5, '0')}`,
    created_at: new Date().toISOString(),
    raw_text: '',
    photo_url: null,
    lat: null,
    lng: null,
    address: null,
    reporter_contact: null,
    category: null,
    subcategory: null,
    hazard_flags: [],
    classifier_confidence: null,
    issue_id: null,
    ...fields,
  }
  state.reports.push(report)
  dirty.state.add('counters')
  markDirty('reports', report.report_id)
  return report
}

export function updateReport(id, patch) {
  const r = getReport(id)
  if (r) {
    Object.assign(r, patch)
    markDirty('reports', id)
  }
  return r
}

export const getReport = (id) => state.reports.find((r) => r.report_id === id)
export const listReports = () => state.reports
export const reportsForIssue = (issueId) => state.reports.filter((r) => r.issue_id === issueId)

// ---------- issues ----------
export function createIssue(fields) {
  const issue = {
    issue_id: state.next_issue_id++,
    category: null,
    subcategory: null,
    lat: null,
    lng: null,
    address: null,
    neighborhood: null,
    summary: '',
    report_count: 0,
    first_reported_at: null,
    last_reported_at: null,
    priority_score: null,
    priority_tier: null,
    priority_factors: [],
    recommended_department: null,
    recommended_crew: null,
    routing_reason: null,
    suggested_sla_hours: null,
    status: 'new',
    possible_duplicate_of: null,
    hazard_flags: [],
    assigned_crew: null,
    dispatcher_note: null,
    agent_trace: [],
    status_history: [],
    ...fields,
  }
  state.issues.push(issue)
  dirty.state.add('counters')
  markDirty('issues', issue.issue_id)
  return issue
}

export function updateIssue(id, patch) {
  const issue = getIssue(id)
  if (issue) {
    Object.assign(issue, patch)
    markDirty('issues', issue.issue_id)
  }
  return issue
}

export const getIssue = (id) => state.issues.find((i) => i.issue_id === Number(id))
export const listIssues = () => state.issues

// ---------- crews ----------
export const listCrews = () => state.crews
export const getCrew = (id) => state.crews.find((c) => c.crew_id === id)

export function updateCrew(id, patch) {
  const crew = getCrew(id)
  if (crew) {
    Object.assign(crew, typeof patch === 'function' ? patch(crew) : patch)
    markDirty('crews', id)
  }
  return crew
}

// ---------- batch metrics ----------
export const getLastBatch = () => state.last_batch
export function setLastBatch(b) {
  state.last_batch = b
  dirty.state.add('last_batch')
  saveSoon()
}

// ---------- route plans ----------
export const getLastRoutePlan = () => state.last_route_plan
export function setLastRoutePlan(p) {
  state.last_route_plan = p
  dirty.state.add('last_route_plan')
  saveSoon()
}

// ---------- photos ----------
const MIME = { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', webp: 'image/webp', gif: 'image/gif' }

/** Store a photo from a data URL. Returns its URL (/uploads/<name>) or null if it isn't an image. */
export async function savePhoto(dataUrl) {
  const m = /^data:image\/(png|jpe?g|webp|gif);base64,(.+)$/.exec(dataUrl || '')
  if (!m) return null
  const ext = m[1] === 'jpeg' ? 'jpg' : m[1]
  const name = `${randomUUID()}.${ext}`
  await backend.savePhoto(name, MIME[ext], Buffer.from(m[2], 'base64'))
  return `/uploads/${name}`
}

/** { mime, bytes } for a stored photo name, or null. */
export const readPhoto = (name) => backend.readPhoto(name)
