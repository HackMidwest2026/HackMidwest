// MongoDB persistence through Prisma (used when DATABASE_URL is set).
// store.js keeps a fast in-memory working copy for the agents and tools; this module loads
// it at startup and writes every change back. Field names match the API's JSON; fields the
// schema doesn't name are kept in each document's `extra` so nothing is lost.
import { PrismaClient } from '@prisma/client'

// type per field: d = DateTime (ISO string in the app), j = Json, s/n/i/a = plain values.
// A trailing ? marks a field only some records have: it is left out on load when empty.
const FIELDS = {
  issue: {
    issue_id: 'i', status: 's', category: 's', subcategory: 's', summary: 's', address: 's', neighborhood: 's',
    lat: 'n', lng: 'n', report_count: 'i', first_reported_at: 'd', last_reported_at: 'd', priority_score: 'n',
    priority_tier: 's', priority_factors: 'j', recommended_department: 's', recommended_crew: 's', routing_reason: 's',
    suggested_sla_hours: 'i', possible_duplicate_of: 'i', hazard_flags: 'a', assigned_crew: 's', dispatcher_note: 's',
    agent_trace: 'j', status_history: 'j',
  },
  report: {
    report_id: 's', created_at: 'd', raw_text: 's', description: 's?', photo_url: 's', lat: 'n', lng: 'n', address: 's',
    area: 's?', reporter_contact: 's', category_hint: 's?', category: 's', subcategory: 's', hazard_flags: 'a',
    classifier_confidence: 'n', issue_id: 'i', dedup: 'j?', photo_analysis: 'j?', demo_id: 's?', truth: 'j?',
  },
  crew: { crew_id: 's', name: 's', department_id: 's', home_lat: 'n', home_lng: 'n', open_jobs: 'i', capacity: 'i' },
}
const KEY = { issue: 'issue_id', report: 'report_id', crew: 'crew_id' }

/** App object -> Prisma data. Unknown fields go to `extra`. */
export function toDoc(kind, obj) {
  const spec = FIELDS[kind]
  const data = {}
  const extra = {}
  for (const [k, v] of Object.entries(obj)) {
    const t = spec[k]?.[0]
    if (!t) {
      if (v !== undefined) extra[k] = v
    } else if (t === 'd') data[k] = v ? new Date(v) : null
    else if (t === 'j') data[k] = v ?? null
    else if (t === 'a') data[k] = Array.isArray(v) ? v : []
    else if (t === 'i') data[k] = v == null ? null : Math.round(Number(v))
    else data[k] = v ?? null
  }
  data.extra = Object.keys(extra).length ? extra : null
  return data
}

/** Prisma record -> app object (ISO date strings, `extra` merged back, db ids dropped). */
export function fromDoc(kind, doc) {
  const spec = FIELDS[kind]
  const obj = {}
  for (const [k, t] of Object.entries(spec)) {
    const v = doc[k]
    if (v == null && t.endsWith('?')) continue
    obj[k] = t === 'd' ? (v ? new Date(v).toISOString() : null) : v ?? (t === 'a' ? [] : null)
  }
  return { ...obj, ...(doc.extra && typeof doc.extra === 'object' ? doc.extra : {}) }
}

// The indexes from prisma/schema.prisma, named as `prisma db push` names them, so a new,
// empty database works without running the Prisma CLI first. Creating an index that
// already exists is a no-op.
const INDEXES = {
  issues: [['issue_id', true], ['status'], ['priority_score'], ['updated_at']],
  reports: [['report_id', true], ['issue_id'], ['updated_at']],
  crews: [['crew_id', true], ['updated_at']],
  photos: [['name', true]],
  app_state: [['key', true]],
  counters: [['name', true]],
  users: [['user_id', true], ['email', true]],
}

// Numbering starts after these (first issue #1040, first report R-00001).
export const ID_BASE = { issue: 1039, report: 0 }

const isUniqueViolation = (err) => err?.code === 'P2002' || /duplicate key|E11000/i.test(err?.message || '')

async function ensureIndexes(prisma) {
  for (const [collection, list] of Object.entries(INDEXES)) {
    await prisma.$runCommandRaw({
      createIndexes: collection,
      indexes: list.map(([field, unique]) => ({
        key: { [field]: 1 },
        name: `${collection}_${field}_${unique ? 'key' : 'idx'}`,
        ...(unique ? { unique: true } : {}),
      })),
    })
  }
}

export function createMongoBackend(url) {
  const prisma = new PrismaClient({ datasources: { db: { url } } })
  const model = { issue: prisma.issue, report: prisma.report, crew: prisma.crew }

  /**
   * Make sure each counter exists and is past every id already stored (including ids from
   * before counters existed, kept in app_state.counters), so numbering never reuses one.
   */
  async function ensureCounters() {
    const [lastIssue, lastReport, legacy] = await Promise.all([
      prisma.issue.findFirst({ orderBy: { issue_id: 'desc' }, select: { issue_id: true } }),
      prisma.report.findFirst({ orderBy: { report_id: 'desc' }, select: { report_id: true } }),
      prisma.appState.findUnique({ where: { key: 'counters' } }),
    ])
    const floor = {
      issue: Math.max(ID_BASE.issue, lastIssue?.issue_id ?? 0, (legacy?.value?.next_issue_id ?? 0) - 1),
      report: Math.max(ID_BASE.report, Number(lastReport?.report_id?.replace(/\D/g, '') || 0), (legacy?.value?.next_report_id ?? 0) - 1),
    }
    for (const [name, value] of Object.entries(floor)) {
      try {
        await prisma.counter.create({ data: { name, value } })
      } catch (err) {
        if (!isUniqueViolation(err)) throw err // another instance created it first: fine
      }
      await prisma.counter.updateMany({ where: { name, value: { lt: value } }, data: { value } })
    }
  }

  async function upsert(kind, obj) {
    const data = toDoc(kind, obj)
    const where = { [KEY[kind]]: obj[KEY[kind]] }
    await model[kind].upsert({ where, create: data, update: data })
  }

  return {
    name: 'mongodb',
    async connect() {
      await prisma.$connect()
      // Also the first round trip, so a bad URL or blocked IP fails at startup, not on the first report.
      await ensureIndexes(prisma)
      await ensureCounters()
    },
    /**
     * Hand out `n` new ids of a kind ("issue" or "report"). The counter is incremented
     * atomically in the database, so every API instance gets different numbers.
     */
    async allocate(kind, n = 1) {
      const c = await prisma.counter.update({ where: { name: kind }, data: { value: { increment: n } } })
      return Array.from({ length: n }, (_, i) => c.value - n + 1 + i)
    },
    /**
     * Records changed by any instance at or after `since` (a Date), plus the reset epoch and
     * small shared values. Used to keep each instance's working copy in sync.
     */
    async changesSince(since) {
      const where = { updated_at: { gte: since } }
      const [issues, reports, crews, state] = await Promise.all([
        prisma.issue.findMany({ where, orderBy: { updated_at: 'asc' } }),
        prisma.report.findMany({ where, orderBy: { updated_at: 'asc' } }),
        prisma.crew.findMany({ where }),
        prisma.appState.findMany({ where: { key: { in: ['epoch', 'last_batch', 'last_route_plan'] } } }),
      ])
      const kv = Object.fromEntries(state.map((x) => [x.key, x.value]))
      const stamps = [...issues, ...reports, ...crews].map((d) => d.updated_at.getTime())
      return {
        issues: issues.map((d) => fromDoc('issue', d)),
        reports: reports.map((d) => fromDoc('report', d)),
        crews: crews.map((d) => fromDoc('crew', d)),
        latest: stamps.length ? Math.max(...stamps) : null,
        epoch: kv.epoch ?? null,
        last_batch: kv.last_batch ?? null,
        last_route_plan: kv.last_route_plan ?? null,
      }
    },
    async load() {
      const [issues, reports, crews, state] = await Promise.all([
        prisma.issue.findMany({ orderBy: { issue_id: 'asc' } }),
        prisma.report.findMany({ orderBy: { created_at: 'asc' } }),
        prisma.crew.findMany(),
        prisma.appState.findMany(),
      ])
      const kv = Object.fromEntries(state.map((s) => [s.key, s.value]))
      if (issues.length === 0 && reports.length === 0) return { epoch: kv.epoch ?? null, empty: true } // nothing to load yet
      return {
        epoch: kv.epoch ?? null,
        issues: issues.map((d) => fromDoc('issue', d)),
        reports: reports.map((d) => fromDoc('report', d)),
        crews: crews.map((d) => fromDoc('crew', d)),
        last_batch: kv.last_batch ?? null,
        last_route_plan: kv.last_route_plan ?? null,
      }
    },
    /** Write the changed records. changes: { issues, reports, crews: [obj], state: {key: value} } */
    async save(changes) {
      const jobs = [
        ...changes.issues.map((o) => () => upsert('issue', o)),
        ...changes.reports.map((o) => () => upsert('report', o)),
        ...changes.crews.map((o) => () => upsert('crew', o)),
        ...Object.entries(changes.state).map(([key, value]) => () =>
          prisma.appState.upsert({ where: { key }, create: { key, value: value ?? null }, update: { value: value ?? null } }),
        ),
      ]
      // A few at a time: fast enough for a batch of 50 reports, gentle on a free M0 cluster.
      for (let i = 0; i < jobs.length; i += 8) await Promise.all(jobs.slice(i, i + 8).map((j) => j()))
    },
    /**
     * Delete all CityCare data (demo reset) and restart numbering. Writes a new `epoch` so
     * other instances notice the reset and reload. Photos are kept; reports may link to them.
     */
    async clear(epoch) {
      // Accounts and the session-signing secret survive a demo reset.
      await Promise.all([prisma.issue.deleteMany(), prisma.report.deleteMany(), prisma.crew.deleteMany(), prisma.appState.deleteMany({ where: { key: { not: 'auth_secret' } } })])
      for (const [name, value] of Object.entries(ID_BASE)) await prisma.counter.updateMany({ where: { name }, data: { value } })
      await prisma.appState.upsert({ where: { key: 'epoch' }, create: { key: 'epoch', value: epoch }, update: { value: epoch } })
    },
    // ---------- dispatcher accounts ----------
    async findUser({ email, user_id }) {
      const u = await prisma.user.findUnique({ where: email ? { email } : { user_id } })
      return u && { user_id: u.user_id, email: u.email, name: u.name, password_hash: u.password_hash, role: u.role, created_at: u.created_at.toISOString() }
    },
    /** Returns false if the email is already taken. */
    async createUser(user) {
      try {
        await prisma.user.create({ data: { ...user, created_at: new Date(user.created_at) } })
        return true
      } catch (err) {
        if (isUniqueViolation(err)) return false
        throw err
      }
    },
    /** The secret that signs login sessions: created once, shared by every instance. */
    async authSecret(candidate) {
      try {
        await prisma.appState.create({ data: { key: 'auth_secret', value: candidate } })
      } catch (err) {
        if (!isUniqueViolation(err)) throw err
      }
      return (await prisma.appState.findUnique({ where: { key: 'auth_secret' } })).value
    },
    async savePhoto(name, mime, bytes) {
      await prisma.photo.upsert({ where: { name }, create: { name, mime, data: bytes }, update: { mime, data: bytes } })
    },
    async readPhoto(name) {
      const p = await prisma.photo.findUnique({ where: { name } })
      return p ? { mime: p.mime, bytes: Buffer.from(p.data) } : null
    },
    disconnect: () => prisma.$disconnect(),
  }
}
