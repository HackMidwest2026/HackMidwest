// Plain JS data tools. The rule-based (mock) agents call these directly, and
// tools/strandsTools.js wraps the same functions as Strands tools for the LLM agents.
import { config } from '../config.js'
import { categories, departments, findDepartment } from '../lib/data.js'
import {
  distanceM,
  nearbySensitiveSites as sitesNear,
  neighborhoodFor,
  roadType,
} from '../lib/geo.js'
import { getIssue as storeGetIssue, listCrews, listIssues, listReports, reportsForIssue } from '../lib/store.js'
import { similarity } from '../lib/text.js'
import { describePoint, locateText } from '../lib/locate.js'

const OPEN_STATUSES = new Set(['new', 'triaged', 'approved', 'assigned', 'in_progress'])
const DAY_MS = 86400000

export function listCategories() {
  return categories.map((c) => ({
    category: c.id,
    name: c.name,
    subcategories: c.subcategories.map((s) => ({ id: s.id, name: s.name, safety_hazard: s.hazard })),
  }))
}

// Any location: local city data first, then OpenStreetMap.
export const geocodeAddress = async ({ text }) => (await locateText(text)) || { found: false, reason: 'Place not found.' }
export const reverseGeocode = ({ lat, lng }) => describePoint({ lat, lng })

export function analyzePhoto({ photo_url }) {
  // Rule-based stand-in. In Bedrock mode the Vision agent (agents/photo.js) analyzes the photo instead.
  return { analyzed: false, photo_url, note: 'Photo stored for the dispatcher; photo analysis runs in Bedrock mode.' }
}

function issueBrief(issue, origin, text) {
  const ageDays = (Date.now() - new Date(issue.first_reported_at).getTime()) / DAY_MS
  return {
    issue_id: issue.issue_id,
    category: issue.category,
    subcategory: issue.subcategory,
    summary: issue.summary,
    address: issue.address,
    report_count: issue.report_count,
    status: issue.status,
    days_open: +ageDays.toFixed(1),
    ...(origin && { distance_m: Math.round(distanceM(origin, issue)) }),
    ...(text && { text_similarity: +similarity(text, issueText(issue)).toFixed(2) }),
  }
}

function issueText(issue) {
  return [issue.summary, ...reportsForIssue(issue.issue_id).map((r) => r.raw_text)].join(' ')
}

/** Code-based candidate filter for dedup: open issues within radius and time window, optionally same category. */
export function findNearbyIssues({ lat, lng, radius_m = config.dedup.radiusM, days = config.dedup.windowDays, category, text }) {
  const since = Date.now() - days * DAY_MS
  return listIssues()
    .filter((i) => OPEN_STATUSES.has(i.status))
    .filter((i) => !category || i.category === category)
    .filter((i) => new Date(i.last_reported_at).getTime() >= since)
    .map((i) => issueBrief(i, { lat, lng }, text))
    .filter((i) => i.distance_m <= radius_m)
    .sort((a, b) => a.distance_m - b.distance_m)
}

export function semanticSearchIssues({ text, top_k = 5 }) {
  return listIssues()
    .filter((i) => OPEN_STATUSES.has(i.status))
    .map((i) => ({ ...issueBrief(i), score: +similarity(text, issueText(i)).toFixed(2) }))
    .filter((i) => i.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, top_k)
}

export function getIssue({ issue_id }) {
  const issue = storeGetIssue(issue_id)
  if (!issue) return { error: `Issue ${issue_id} not found` }
  return {
    ...issueBrief(issue),
    lat: issue.lat,
    lng: issue.lng,
    neighborhood: issue.neighborhood,
    priority_score: issue.priority_score,
    priority_tier: issue.priority_tier,
    recommended_department: issue.recommended_department,
    reports: reportsForIssue(issue.issue_id).map((r) => ({ report_id: r.report_id, created_at: r.created_at, text: r.raw_text })),
  }
}

export const getRoadType = ({ lat, lng }) => roadType({ lat, lng })
export const nearbySensitiveSites = ({ lat, lng, radius_m = 200 }) => sitesNear({ lat, lng }, radius_m)

export function getIssueHistory({ issue_id }) {
  const issue = storeGetIssue(issue_id)
  if (!issue) return { error: `Issue ${issue_id} not found` }
  return {
    issue_id: issue.issue_id,
    report_count: issue.report_count,
    first_reported_at: issue.first_reported_at,
    last_reported_at: issue.last_reported_at,
    days_open: +((Date.now() - new Date(issue.first_reported_at).getTime()) / DAY_MS).toFixed(1),
    hazard_flags: issue.hazard_flags,
    status_history: issue.status_history,
  }
}

export function listDepartments() {
  return departments.map((d) => ({ department_id: d.department_id, name: d.name, categories_handled: d.categories_handled }))
}

export function getCrewWorkload({ department_id }) {
  return listCrews()
    .filter((c) => !department_id || c.department_id === department_id)
    .map((c) => ({
      crew_id: c.crew_id,
      name: c.name,
      department_id: c.department_id,
      open_jobs: c.open_jobs,
      capacity: c.capacity,
      utilization: +(c.open_jobs / c.capacity).toFixed(2),
    }))
}

export function getCrewLocations({ department_id, lat, lng }) {
  return listCrews()
    .filter((c) => !department_id || c.department_id === department_id)
    .map((c) => ({
      crew_id: c.crew_id,
      name: c.name,
      home_lat: c.home_lat,
      home_lng: c.home_lng,
      ...(lat != null && lng != null && { distance_km: +(distanceM({ lat, lng }, { lat: c.home_lat, lng: c.home_lng }) / 1000).toFixed(1) }),
    }))
    .sort((a, b) => (a.distance_km ?? 0) - (b.distance_km ?? 0))
}

/** Supervisor query tool: filter and rank issues. */
export function queryIssues({ neighborhood, category, tier, status = 'open', hazard_only = false, limit = 10 } = {}) {
  return listIssues()
    .filter((i) => (status === 'open' ? OPEN_STATUSES.has(i.status) : status === 'any' || i.status === status))
    .filter((i) => !neighborhood || (i.neighborhood || '').toLowerCase().includes(neighborhood.toLowerCase()))
    .filter((i) => !category || i.category === category)
    .filter((i) => !tier || i.priority_tier === tier)
    .filter((i) => !hazard_only || i.hazard_flags.length > 0 || i.priority_factors.some((f) => f.factor === 'safety_hazard'))
    .sort((a, b) => (b.priority_score ?? 0) - (a.priority_score ?? 0))
    .slice(0, limit)
    .map((i) => ({
      issue_id: i.issue_id,
      summary: i.summary,
      address: i.address,
      neighborhood: i.neighborhood,
      category: i.category,
      subcategory: i.subcategory,
      priority_score: i.priority_score,
      priority_tier: i.priority_tier,
      report_count: i.report_count,
      status: i.status,
      recommended_department: i.recommended_department ? findDepartment(i.recommended_department)?.name : null,
      hazard_flags: i.hazard_flags,
    }))
}

export function getStats() {
  const issues = listIssues()
  const open = issues.filter((i) => OPEN_STATUSES.has(i.status))
  const count = (arr, key) => arr.reduce((m, i) => ((m[i[key] ?? 'unscored'] = (m[i[key] ?? 'unscored'] || 0) + 1), m), {})
  const reports = issues.reduce((s, i) => s + i.report_count, 0)
  return {
    total_issues: issues.length,
    open_issues: open.length,
    total_reports: reports,
    duplicate_reduction_pct: reports ? Math.round((1 - issues.length / reports) * 100) : 0,
    reports_last_24h: listReports().filter((r) => Date.now() - new Date(r.created_at).getTime() < 86400000).length,
    awaiting_approval: open.filter((i) => ['new', 'triaged'].includes(i.status)).length,
    open_by_tier: count(open, 'priority_tier'),
    open_by_category: count(open, 'category'),
    open_by_neighborhood: count(open, 'neighborhood'),
    open_by_status: count(open, 'status'),
  }
}

export { neighborhoodFor }
