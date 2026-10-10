// In-memory store persisted to a JSON file. Plenty for hackathon scale; the functions
// below are the only way the rest of the app touches state, so swapping in SQLite or
// DynamoDB later means rewriting this file only.
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { config } from '../config.js'
import { crewSeed } from './data.js'

const statePath = () => join(config.stateDir, 'state.json')

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
let saveTimer = null

export function loadState() {
  mkdirSync(config.stateDir, { recursive: true })
  if (existsSync(statePath())) {
    state = { ...emptyState(), ...JSON.parse(readFileSync(statePath(), 'utf8')) }
    return true
  }
  return false
}

export function saveSoon() {
  if (saveTimer) return
  saveTimer = setTimeout(() => {
    saveTimer = null
    saveNow()
  }, 200)
}

export function saveNow() {
  mkdirSync(config.stateDir, { recursive: true })
  const tmp = `${statePath()}.tmp`
  writeFileSync(tmp, JSON.stringify(state))
  renameSync(tmp, statePath())
}

export function resetState() {
  state = emptyState()
  saveSoon()
}

// ---- reports ----
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
  saveSoon()
  return report
}

export function updateReport(id, patch) {
  const r = getReport(id)
  if (r) Object.assign(r, patch)
  saveSoon()
  return r
}

export const getReport = (id) => state.reports.find((r) => r.report_id === id)
export const listReports = () => state.reports
export const reportsForIssue = (issueId) => state.reports.filter((r) => r.issue_id === issueId)

// ---- issues ----
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
  saveSoon()
  return issue
}

export function updateIssue(id, patch) {
  const issue = getIssue(id)
  if (issue) Object.assign(issue, patch)
  saveSoon()
  return issue
}

export const getIssue = (id) => state.issues.find((i) => i.issue_id === Number(id))
export const listIssues = () => state.issues

// ---- crews ----
export const listCrews = () => state.crews
export const getCrew = (id) => state.crews.find((c) => c.crew_id === id)

// ---- batch metrics ----
export const getLastBatch = () => state.last_batch
export function setLastBatch(b) {
  state.last_batch = b
  saveSoon()
}

// ---- route plans ----
export const getLastRoutePlan = () => state.last_route_plan
export function setLastRoutePlan(p) {
  state.last_route_plan = p
  saveSoon()
}
