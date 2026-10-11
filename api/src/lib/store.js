// The app's data layer. Everything reads and writes state through these functions.
//
// Storage backends:
//   - MongoDB through Prisma when DATABASE_URL is set: the central database. (see lib/mongo.js)
//   - A JSON file under STATE_DIR otherwise: offline demos and tests.
//
// Reads are served from an in-memory working copy (the agents and tools query it many times
// per report, synchronously). Every change marks its record dirty, and dirty records are
// written to the backend shortly after, in order, with retries if the database is
// unreachable.
//
// Several API instances can share one MongoDB database (say, each teammate running the app):
// issue and report numbers come from atomic counters in the database, and each instance
// pulls the others' changes every few seconds (startSync), so everyone sees the same issues.
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { readFile, writeFile } from 'node:fs/promises'
import { randomUUID } from 'node:crypto'
import { isDeepStrictEqual } from 'node:util'
import { join } from 'node:path'
import { config } from '../config.js'
import { crewSeed } from './data.js'

const FLUSH_DELAY_MS = 150
const RETRY_DELAY_MS = 5000
// Re-read changes this far back on every poll, to cover writes that land slightly out of
// order or from machines whose clocks differ a little.
const SYNC_OVERLAP_MS = 10000

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
    async findUser({ email, user_id }) {
      return (state.users || []).find((u) => (email ? u.email === email : u.user_id === user_id)) || null
    },
    async createUser(user) {
      state.users ||= []
      if (state.users.some((u) => u.email === user.email)) return false
      state.users.push(user)
      saveSoon()
      dirty.state.add('users')
      return true
    },
    async authSecret(candidate) {
      if (!state.auth_secret) {
        state.auth_secret = candidate
        dirty.state.add('auth_secret')
        saveSoon()
      }
      return state.auth_secret
    },
    // One process owns the file, so a local counter is enough.
    async allocate(kind, n = 1) {
      const key = kind === 'issue' ? 'next_issue_id' : 'next_report_id'
      const first = state[key]
      state[key] += n
      dirty.state.add('counters')
      saveSoon()
      return Array.from({ length: n }, (_, i) => first + i)
    },
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
// Records being written right now; sync leaves them alone until the write lands.
const inflight = { issues: new Set(), reports: new Set(), crews: new Set() }
let clearPending = false
let flushTimer = null
let chain = Promise.resolve()
let lastError = null
let retryTimer = null
let closing = false
// Changes the shared database's `epoch` on every demo reset; a different value means another
// instance reset the data.
let epoch = null

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
  for (const k of ['issues', 'reports', 'crews']) taken[k].forEach((id) => inflight[k].add(id))
  // Snapshot so later in-memory edits during the await don't race the write.
  const changes = {
    issues: taken.issues.map(getIssue).filter(Boolean).map((o) => structuredClone(o)),
    reports: taken.reports.map(getReport).filter(Boolean).map((o) => structuredClone(o)),
    crews: taken.crews.map(getCrew).filter(Boolean).map((o) => structuredClone(o)),
    state: Object.fromEntries(taken.state.map((k) => [k, structuredClone(stateValue(k))])),
  }
  try {
    if (wasClear) await backend.clear(epoch)
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
  } finally {
    for (const k of ['issues', 'reports', 'crews']) taken[k].forEach((id) => inflight[k].delete(id))
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
  syncCursor = Date.now()
  epoch = saved?.epoch ?? null
  if (!saved || saved.empty) return false
  state = { ...emptyState(), ...saved }
  delete state.epoch
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

// ---------- sync between instances sharing a database ----------

const listeners = new Set()
let syncTimer = null
let syncing = false
let syncCursor = 0
let syncError = null

/** Changes made by other instances: fn({ type: 'issue', issue }) or fn({ type: 'reload' }). */
export function onRemoteChange(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

const emit = (event) => listeners.forEach((fn) => fn(event))

/** Poll the database for other instances' changes every `intervalMs`. No-op for the file backend. */
export function startSync(intervalMs) {
  if (!backend.changesSince || !(intervalMs > 0) || syncTimer) return false
  syncTimer = setInterval(() => {
    syncOnce().catch((err) => {
      const msg = `${err.name}: ${err.message}`
      if (msg !== syncError) console.error('[store] sync with the database failed (will keep trying):', msg)
      syncError = msg
    })
  }, intervalMs)
  syncTimer.unref?.()
  return true
}

export function stopSync() {
  clearInterval(syncTimer)
  syncTimer = null
}

const plain = (o) => JSON.parse(JSON.stringify(o))
const sameJson = (a, b) => isDeepStrictEqual(plain(a), plain(b))

/** Copy a record from the database into the working copy. Returns true if anything changed. */
function applyRemote(kind, list, key, remote) {
  const id = remote[key]
  if (dirty[kind].has(id) || inflight[kind].has(id)) return false // our newer version wins
  const local = list.find((x) => x[key] === id)
  if (!local) {
    list.push(remote)
    return true
  }
  if (sameJson(local, remote)) return false
  // Update in place: code holding this object (an agent step in progress) sees the new values.
  for (const k of Object.keys(local)) if (!(k in remote)) delete local[k]
  Object.assign(local, remote)
  return true
}

/** One sync pass: pull records other instances changed and announce them. */
export async function syncOnce() {
  if (syncing || !backend.changesSince || clearPending) return
  syncing = true
  try {
    const c = await backend.changesSince(new Date(syncCursor - SYNC_OVERLAP_MS))
    if (clearPending) return // a reset started meanwhile; its data wins
    if (c.epoch && c.epoch !== epoch) {
      // Another instance reset the demo: start over from what the database holds now.
      const saved = await backend.load()
      state = { ...emptyState(), ...(saved && !saved.empty ? saved : {}) }
      delete state.epoch
      delete state.empty
      epoch = saved?.epoch ?? c.epoch
      for (const s of Object.values(dirty)) s.clear()
      idPool.issue = []
      idPool.report = []
      syncCursor = Date.now()
      emit({ type: 'reload' })
      return
    }
    if (c.latest) syncCursor = Math.max(syncCursor, c.latest)
    const touched = new Set()
    for (const r of c.reports) if (applyRemote('reports', state.reports, 'report_id', r) && r.issue_id != null) touched.add(r.issue_id)
    for (const i of c.issues) if (applyRemote('issues', state.issues, 'issue_id', i)) touched.add(i.issue_id)
    for (const cr of c.crews) applyRemote('crews', state.crews, 'crew_id', cr)
    for (const k of ['last_batch', 'last_route_plan']) {
      if (!dirty.state.has(k) && c[k] != null && !sameJson(state[k], c[k])) state[k] = c[k]
    }
    syncError = null
    for (const id of touched) {
      const issue = getIssue(id)
      if (issue) emit({ type: 'issue', issue })
    }
  } finally {
    syncing = false
  }
}

export async function closeStore() {
  stopSync()
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

/**
 * Wipe all data and start over with the seed crews (demo reset). Resolves once the database
 * is wiped and numbering restarted, so await it before creating new records.
 */
export function resetState() {
  // Dispatcher accounts and the session secret (file backend) survive a demo reset.
  state = { ...emptyState(), ...(state.users && { users: state.users }), ...(state.auth_secret && { auth_secret: state.auth_secret }) }
  for (const s of Object.values(dirty)) s.clear()
  clearPending = true
  epoch = randomUUID() // tells other instances sharing the database to reload
  idPool.issue = []
  idPool.report = []
  syncCursor = Date.now()
  state.crews.forEach((c) => dirty.crews.add(c.crew_id))
  ;['counters', 'last_batch', 'last_route_plan'].forEach((k) => dirty.state.add(k))
  return flush()
}

// ---------- ids ----------

const idPool = { issue: [], report: [] }

/** Reserve `n` ids ahead of a batch (one database round trip instead of n). */
export async function reserveIds(kind, n) {
  if (n > 0) idPool[kind].push(...(await backend.allocate(kind, n)))
}

async function takeId(kind) {
  return idPool[kind].shift() ?? (await backend.allocate(kind, 1))[0]
}

// ---------- reports ----------
export async function createReport(fields) {
  const report = {
    report_id: `R-${String(await takeId('report')).padStart(5, '0')}`,
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
export async function createIssue(fields) {
  const issue = {
    issue_id: await takeId('issue'),
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

// ---------- dispatcher accounts (read straight from the backend, so every instance agrees) ----------

/** { user_id, email, name, password_hash, role, created_at } or null. */
export const findUser = (query) => backend.findUser(query)
/** Store a new account. Resolves false if the email is taken. */
export const createUser = (user) => backend.createUser(user)
/** The session-signing secret: `candidate` unless one was already stored. */
export const authSecret = (candidate) => backend.authSecret(candidate)

/** { mime, bytes } for a stored photo name, or null. */
export const readPhoto = (name) => backend.readPhoto(name)
