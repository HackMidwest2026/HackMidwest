// Route Planner agent (Sonnet-class). Groups each crew's open jobs into trips for today's
// shift: urgent jobs first, nearby low-priority jobs ride along instead of waiting for a
// separate trip, and what does not fit is deferred. Code orders the stops and does the
// time math (lib/routing.js); the agent makes the grouping calls and explains them.
import { randomUUID } from 'node:crypto'
import { z } from 'zod'
import { cityLabel } from '../lib/data.js'
import { distanceM } from '../lib/geo.js'
import { emitTrace } from '../lib/events.js'
import { crewsWithJobs, driveMinutes, estimateRoute, SHIFT_MINUTES, tripHeadline } from '../lib/routing.js'
import { makeTools, runStructured } from './llm.js'
import { RoutePlanOutput } from './schemas.js'
import { runStep } from './step.js'

const SYSTEM_PROMPT = `You are the Route Planner agent for CityCare, a city 311 operations system serving ${cityLabel}.
You get every field crew that has open jobs, with each job's priority, location, on-site minutes, drive time from the crew's yard and nearby jobs.
Plan today's shift for each crew (${SHIFT_MINUTES} minutes including driving and the drive back to the yard):
- P1 and P2 jobs go on today's trip.
- Bundle P3/P4 jobs that sit near a job the crew is already visiting ("ride-alongs") instead of leaving them for a separate trip later.
- If a crew's jobs do not fit in one shift, defer the lowest-priority, most out-of-the-way jobs, with a reason.
- Jobs marked needs_approval are still recommendations; you may plan them, but mention it.
Call estimate_route to check a trip's total minutes when it might be close to the shift limit. Code optimizes the stop order, so only choose which jobs go together.
Every job must appear in exactly one trip or in deferred. In the summary, do not state counts or total minutes; the dashboard shows exact totals. Finish by calling the structured output tool; do not reply in plain text.`

const toolSpecs = [
  {
    name: 'estimate_route',
    description: "Time a trip for one crew (yard -> jobs -> yard): stop order, drive, on-site and total minutes, and whether it exceeds the shift.",
    input: z.object({ crew_id: z.string(), issue_ids: z.array(z.number().int()) }),
    fn: ({ crew_id, issue_ids }) => {
      const r = estimateRoute(crew_id, issue_ids)
      return r.error ? r : { ...r, stops: r.stops.map((s) => ({ issue_id: s.issue_id, arrive_min: s.arrive_min, work_min: s.work_min })) }
    },
  },
]

const TIER_RANK = { P1: 0, P2: 1, P3: 2, P4: 3 }

/** Rule-based planner: urgent first, then nearest from the yard, packed until the shift is full. */
function mockPlan(crews) {
  const trips = []
  const deferred = []
  for (const c of crews) {
    const jobs = [...c.jobs].sort((a, b) => (TIER_RANK[a.priority_tier] ?? 3) - (TIER_RANK[b.priority_tier] ?? 3) || a.drive_from_yard_min - b.drive_from_yard_min)
    const ids = []
    for (const j of jobs) {
      if (estimateRoute(c.crew_id, [...ids, j.issue_id]).total_min <= SHIFT_MINUTES || ids.length === 0) ids.push(j.issue_id)
      else deferred.push({ issue_id: j.issue_id, reason: `Does not fit in today's ${SHIFT_MINUTES / 60}-hour shift for ${c.name}.` })
    }
    trips.push({ crew_id: c.crew_id, issue_ids: ids, reason: 'Urgent jobs first, then the nearest remaining jobs until the shift is full.' })
  }
  return { trips, deferred, summary: `Planned ${trips.length} crew trips by priority and distance.` }
}

/** Validate the agent's grouping against real crew jobs and compute the final timings. */
function finalize(crews, out) {
  const jobsOf = new Map(crews.map((c) => [c.crew_id, new Map(c.jobs.map((j) => [j.issue_id, j]))]))
  const seen = new Set()
  const trips = []
  for (const t of out.trips) {
    const mine = jobsOf.get(t.crew_id)
    if (!mine) continue
    const ids = t.issue_ids.filter((id) => mine.has(id) && !seen.has(id))
    if (!ids.length) continue
    ids.forEach((id) => seen.add(id))
    const route = estimateRoute(t.crew_id, ids)
    const urgent = route.stops.filter((s) => (TIER_RANK[s.priority_tier] ?? 3) <= 1)
    trips.push({
      ...route,
      headline: tripHeadline(route),
      reason: t.reason,
      needs_approval_count: route.stops.filter((s) => s.needs_approval).length,
      // Low-priority stops within 1 km of an urgent stop on the same trip.
      ride_along_ids: route.stops
        .filter((s) => (TIER_RANK[s.priority_tier] ?? 3) >= 2 && urgent.some((u) => distanceM(u, s) <= 1000))
        .map((s) => s.issue_id),
    })
  }
  const crewOf = new Map(crews.flatMap((c) => c.jobs.map((j) => [j.issue_id, c.crew_id])))
  const deferred = out.deferred.filter((d) => crewOf.has(d.issue_id) && !seen.has(d.issue_id))
  deferred.forEach((d) => seen.add(d.issue_id))
  for (const [id, crewId] of crewOf) if (!seen.has(id)) deferred.push({ issue_id: id, reason: 'Not scheduled by the planner.', crew_id: crewId })

  const drive = trips.reduce((s, t) => s + t.drive_min, 0)
  // Baseline: every planned job as its own round trip from the crew's yard.
  const naive = trips.reduce((s, t) => s + t.stops.reduce((a, j) => a + 2 * driveMinutes(t.home, j), 0), 0)
  return {
    summary: out.summary,
    trips,
    deferred: deferred.map((d) => ({ ...d, crew_id: d.crew_id ?? crewOf.get(d.issue_id) })),
    totals: {
      crews: trips.length,
      jobs: trips.reduce((s, t) => s + t.stops.length, 0),
      deferred: deferred.length,
      drive_min: drive,
      naive_drive_min: naive,
      drive_saved_min: Math.max(0, naive - drive),
    },
  }
}

export async function planRoutes({ runId = randomUUID() } = {}) {
  const crews = crewsWithJobs()
  const ctx = { trace: (evt) => emitTrace({ run_id: runId, ...evt }) }
  const plan = await runStep({
    agent: 'routes',
    ctx,
    startMessage: `Planning today's routes for ${crews.length} crew${crews.length === 1 ? '' : 's'} with ${crews.reduce((s, c) => s + c.jobs.length, 0)} open jobs.`,
    mock: () => ({ ...finalize(crews, mockPlan(crews)), engine: 'mock' }),
    llm: async (onTool) => {
      const { output, modelId } = await runStructured({
        name: 'routes',
        tier: 'reasoning',
        systemPrompt: SYSTEM_PROMPT,
        tools: makeTools(toolSpecs, onTool),
        schema: RoutePlanOutput,
        prompt: JSON.stringify({
          shift_minutes: SHIFT_MINUTES,
          crews: crews.map((c) => ({
            crew_id: c.crew_id,
            name: c.name,
            jobs: c.jobs.map(({ lat, lng, ...j }) => j),
          })),
        }),
      })
      return { output: { ...finalize(crews, output), engine: 'bedrock', model: modelId }, modelId }
    },
    summarize: (p) =>
      `${p.totals.jobs} jobs on ${p.trips.length} crew trips, ${p.totals.deferred} deferred. ` +
      `Bundling saves about ${p.totals.drive_saved_min} min of driving vs one trip per job.`,
  })
  return { plan_id: runId, run_id: runId, created_at: new Date().toISOString(), crews_considered: crews.length, ...plan }
}
