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
  issues: [['issue_id', true], ['status'], ['priority_score']],
  reports: [['report_id', true], ['issue_id']],
  crews: [['crew_id', true]],
  photos: [['name', true]],
  app_state: [['key', true]],
}

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
    },
    async load() {
      const [issues, reports, crews, state] = await Promise.all([
        prisma.issue.findMany({ orderBy: { issue_id: 'asc' } }),
        prisma.report.findMany({ orderBy: { created_at: 'asc' } }),
        prisma.crew.findMany(),
        prisma.appState.findMany(),
      ])
      const kv = Object.fromEntries(state.map((s) => [s.key, s.value]))
      if (!kv.counters && issues.length === 0 && reports.length === 0) return null // empty database
      return {
        ...(kv.counters || {}),
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
    /** Delete all CityCare data (demo reset). Photos are kept; reports may still link to them. */
    async clear() {
      await Promise.all([prisma.issue.deleteMany(), prisma.report.deleteMany(), prisma.crew.deleteMany(), prisma.appState.deleteMany()])
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
