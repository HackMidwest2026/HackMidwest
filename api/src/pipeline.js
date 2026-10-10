// The CityCare pipeline: Intake -> Dedup -> (merge | create) -> Priority -> Router -> dispatcher.
//
// The flow is deterministic, so it is orchestrated in code (a "workflow" over Strands agents)
// rather than letting agents hand off to each other. That keeps it debuggable and lets the
// batch path parallelize the independent steps:
//   single report:  intake -> dedup -> priority -> router
//   batch:          intake (parallel) -> dedup (serial, it mutates issues) -> priority+router per touched issue (parallel)
import { randomUUID } from 'node:crypto'
import { config, isBedrock } from './config.js'
import { runDedup } from './agents/dedup.js'
import { runIntake } from './agents/intake.js'
import { runPriority } from './agents/priority.js'
import { runRouter } from './agents/router.js'
import { subcategoryName } from './agents/rules.js'
import { emitIssueUpdate, emitTrace } from './lib/events.js'
import { neighborhoodFor } from './lib/geo.js'
import { describePoint, locateText } from './lib/locate.js'
import * as store from './lib/store.js'

const TRACE_LIMIT = 200

// ---------- helpers ----------

function makeCtx({ runId, reportId, delay = true, forceMock = false, sink }) {
  return {
    runId,
    delay,
    forceMock,
    issueId: null,
    trace(evt) {
      const full = emitTrace({ run_id: runId, report_id: reportId, issue_id: this.issueId, ...evt })
      sink.push(full)
      return full
    },
  }
}

let dedupChain = Promise.resolve()
/** Dedup + merge must be serialized, or two copies of the same pothole could both create issues. */
function serialized(fn) {
  const next = dedupChain.then(fn, fn)
  dedupChain = next.catch(() => {})
  return next
}

async function mapLimit(items, limit, fn) {
  const out = new Array(items.length)
  let i = 0
  const workers = Array.from({ length: Math.min(limit, items.length) }, async () => {
    while (i < items.length) {
      const idx = i++
      out[idx] = await fn(items[idx], idx)
    }
  })
  await Promise.all(workers)
  return out
}

function attachTrace(issue, events) {
  const trace = [...issue.agent_trace, ...events.map((e) => ({ ...e, issue_id: issue.issue_id }))]
  store.updateIssue(issue.issue_id, { agent_trace: trace.slice(-TRACE_LIMIT) })
}

// ---------- steps ----------

export async function createReportRecord(input) {
  let { lat, lng, address } = input
  let area = input.area || null
  if ((lat == null || lng == null) && input.raw_text) {
    // No pin: try to find the place named in the text (local streets, then OpenStreetMap).
    const found = await locateText(input.raw_text)
    if (found) {
      lat = found.lat
      lng = found.lng
      address ||= found.address
      area ||= found.area
    }
  }
  if (lat == null || lng == null) throw Object.assign(new Error('A location is required: drop a pin or type an address.'), { status: 400 })
  if (!address || !area) {
    const d = await describePoint({ lat: Number(lat), lng: Number(lng) })
    address ||= d.address
    area ||= d.area
  }
  return store.createReport({
    raw_text: String(input.raw_text || '').slice(0, 2000),
    photo_url: input.photo_url || null,
    lat: Number(lat),
    lng: Number(lng),
    address,
    area,
    reporter_contact: input.reporter_contact || null,
    category_hint: input.category_hint || null,
    ...(input.created_at && { created_at: input.created_at }),
    ...(input.demo_id && { demo_id: input.demo_id, truth: input.truth }),
  })
}

async function intakeStep(report, ctx) {
  const out = await runIntake(report, ctx)
  return store.updateReport(report.report_id, {
    category: out.category,
    subcategory: out.subcategory,
    description: out.description,
    hazard_flags: out.hazard_flags,
    classifier_confidence: out.confidence,
  })
}

function mergeInto(issue, report) {
  const n = issue.report_count
  const at = report.created_at
  return store.updateIssue(issue.issue_id, {
    lat: +((issue.lat * n + report.lat) / (n + 1)).toFixed(6),
    lng: +((issue.lng * n + report.lng) / (n + 1)).toFixed(6),
    report_count: n + 1,
    first_reported_at: at < issue.first_reported_at ? at : issue.first_reported_at,
    last_reported_at: at > issue.last_reported_at ? at : issue.last_reported_at,
    hazard_flags: [...new Set([...issue.hazard_flags, ...report.hazard_flags])],
  })
}

function newIssueFrom(report, dedup) {
  return store.createIssue({
    category: report.category,
    subcategory: report.subcategory,
    lat: report.lat,
    lng: report.lng,
    address: report.address,
    neighborhood: neighborhoodFor(report) || report.area || 'Unmapped area',
    summary: issueSummary(report),
    report_count: 1,
    first_reported_at: report.created_at,
    last_reported_at: report.created_at,
    hazard_flags: report.hazard_flags,
    possible_duplicate_of: dedup.possible_duplicate_of ?? null,
    status_history: [{ status: 'new', at: new Date().toISOString(), by: 'pipeline' }],
  })
}

function issueSummary(report) {
  const name = subcategoryName(report.category, report.subcategory)
  const text = report.description || report.raw_text
  const head = name.split(/[ /]/)[0].toLowerCase()
  return text.toLowerCase().includes(head) ? text : `${name}: ${text}`
}

/** Returns { issue, merged }. Runs inside the dedup lock. */
async function dedupStep(report, ctx) {
  return serialized(async () => {
    const dedup = await runDedup(report, ctx)
    const target = dedup.duplicate_of != null ? store.getIssue(dedup.duplicate_of) : null
    const issue = target ? mergeInto(target, report) : newIssueFrom(report, dedup)
    store.updateReport(report.report_id, { issue_id: issue.issue_id, dedup })
    ctx.issueId = issue.issue_id
    emitIssueUpdate(issue)
    return { issue, merged: Boolean(target), dedup }
  })
}

async function triageStep(issueId, ctx) {
  let issue = store.getIssue(issueId)
  const p = await runPriority(issue, ctx)
  issue = store.updateIssue(issueId, {
    priority_score: p.priority_score,
    priority_tier: p.priority_tier,
    priority_factors: p.priority_factors,
  })
  // Once a dispatcher has approved an issue, new reports only re-score it; routing stays as approved.
  if (['new', 'triaged'].includes(issue.status)) {
    const r = await runRouter(issue, ctx)
    issue = store.updateIssue(issueId, {
      recommended_department: r.department_id,
      recommended_crew: r.crew_id,
      routing_reason: r.reason,
      suggested_sla_hours: r.suggested_sla_hours,
      status: 'triaged',
      status_history:
        issue.status === 'new' ? [...issue.status_history, { status: 'triaged', at: new Date().toISOString(), by: 'pipeline' }] : issue.status_history,
    })
  }
  emitIssueUpdate(issue)
  return issue
}

// ---------- public API ----------

export async function processReport(input, { runId = randomUUID(), ...opts } = {}) {
  const events = []
  const report = await createReportRecord(input)
  const ctx = makeCtx({ runId, reportId: report.report_id, sink: events, ...opts })
  ctx.trace({ agent: 'pipeline', status: 'started', message: `Report ${report.report_id} received at ${report.address}.`, data: { lat: report.lat, lng: report.lng } })
  try {
    await intakeStep(report, ctx)
    const { issue, merged } = await dedupStep(store.getReport(report.report_id), ctx)
    const final = await triageStep(issue.issue_id, ctx)
    ctx.trace({
      agent: 'pipeline',
      status: 'completed',
      message: `${merged ? `Merged into issue #${final.issue_id}` : `Created issue #${final.issue_id}`}; awaiting dispatcher approval.`,
      data: { issue_id: final.issue_id, merged },
    })
    attachTrace(final, events)
    return { report: store.getReport(report.report_id), issue: store.getIssue(final.issue_id), merged, run_id: runId }
  } catch (err) {
    ctx.trace({ agent: 'pipeline', status: 'error', message: `Pipeline failed: ${err.message}` })
    throw err
  }
}

/** Batch path. inputs: report inputs (optionally with created_at / truth). */
export async function processBatch(inputs, { forceMock = false, label = 'batch' } = {}) {
  const runId = randomUUID()
  const started = Date.now()
  const events = []
  const batchCtx = makeCtx({ runId, sink: events, delay: false, forceMock })
  batchCtx.trace({ agent: 'pipeline', status: 'started', message: `${label}: ${inputs.length} reports received.` })

  const reports = []
  for (const input of inputs) reports.push(await createReportRecord(input))
  const sinks = new Map(reports.map((r) => [r.report_id, []]))
  const ctxFor = new Map(
    reports.map((r) => [r.report_id, makeCtx({ runId, reportId: r.report_id, sink: sinks.get(r.report_id), delay: false, forceMock })]),
  )
  const llm = isBedrock() && !forceMock

  await mapLimit(reports, llm ? 6 : 50, (r) => intakeStep(r, ctxFor.get(r.report_id)))

  const touched = new Set()
  let merged = 0
  const pace = !llm && !forceMock ? config.mockBatchDelayMs : 0
  for (const r of reports) {
    if (pace) await new Promise((done) => setTimeout(done, pace))
    const res = await dedupStep(store.getReport(r.report_id), ctxFor.get(r.report_id))
    touched.add(res.issue.issue_id)
    if (res.merged) merged++
  }

  const triageSinks = new Map()
  await mapLimit([...touched], llm ? 4 : 50, (id) => {
    const sink = []
    triageSinks.set(id, sink)
    const ctx = makeCtx({ runId, reportId: null, sink, delay: false, forceMock })
    ctx.issueId = id
    return triageStep(id, ctx)
  })

  // Per-report intake/dedup events, then the issue's priority/router events, into each audit trail.
  for (const r of reports) attachTrace(store.getIssue(store.getReport(r.report_id).issue_id), sinks.get(r.report_id))
  for (const [id, sink] of triageSinks) attachTrace(store.getIssue(id), sink)

  const metrics = batchMetrics(reports.map((r) => store.getReport(r.report_id)), touched, merged, Date.now() - started)
  batchCtx.trace({
    agent: 'pipeline',
    status: 'completed',
    message: `${label}: ${metrics.reports} reports → ${metrics.issues} issues (${metrics.duplicate_reduction_pct}% duplicate reduction) in ${(metrics.duration_ms / 1000).toFixed(1)} s.`,
    data: metrics,
  })
  return metrics
}

/** Reduction numbers plus accuracy against ground truth when reports carry `truth`. */
export function batchMetrics(reports, touched, merged, durationMs) {
  const m = {
    reports: reports.length,
    issues: touched.size,
    merged_into_existing_or_batch: merged,
    duplicate_reduction_pct: reports.length ? Math.round((1 - touched.size / reports.length) * 100) : 0,
    duration_ms: durationMs,
    engine: isBedrock() ? 'bedrock' : 'mock',
  }
  const labeled = reports.filter((r) => r.truth)
  if (labeled.length) {
    const catOk = labeled.filter((r) => r.category === r.truth.category).length
    const subOk = labeled.filter((r) => r.subcategory === r.truth.subcategory).length
    let tp = 0
    let fp = 0
    let fn = 0
    for (let i = 0; i < labeled.length; i++) {
      for (let j = i + 1; j < labeled.length; j++) {
        const same = labeled[i].truth.cluster === labeled[j].truth.cluster
        const pred = labeled[i].issue_id === labeled[j].issue_id
        if (same && pred) tp++
        else if (!same && pred) fp++
        else if (same && !pred) fn++
      }
    }
    m.ground_truth = {
      true_issues: new Set(labeled.map((r) => r.truth.cluster)).size,
      category_accuracy: +(catOk / labeled.length).toFixed(3),
      subcategory_accuracy: +(subOk / labeled.length).toFixed(3),
      dedup_precision: tp + fp ? +(tp / (tp + fp)).toFixed(3) : 1,
      dedup_recall: tp + fn ? +(tp / (tp + fn)).toFixed(3) : 1,
    }
  }
  return m
}

export function seedHistory(seedReports) {
  const now = Date.now()
  const inputs = seedReports.map((r) => ({
    ...r,
    created_at: new Date(now - r.days_ago * 86400000 - Math.round(Math.random() * 3600000)).toISOString(),
  }))
  return processBatch(inputs, { forceMock: true, label: 'Seed history' })
}

