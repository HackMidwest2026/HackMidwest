// City Supervisor agent (agents-as-tools): answers dispatcher questions in plain English
// using the data tools plus the Priority and Router agents wrapped as tools.
import { z } from 'zod'
import { city, cityLabel } from '../lib/data.js'
import { getIssue as storeGetIssue, setLastRoutePlan } from '../lib/store.js'
import * as tools from '../tools/cityTools.js'
import { makeTools, runText } from './llm.js'
import { runPriority } from './priority.js'
import { runRouter } from './router.js'
import { planRoutes } from './routes.js'
import { runStep } from './step.js'

const SYSTEM_PROMPT = `You are the City Supervisor agent for CityCare, assisting a 311 dispatcher in ${cityLabel}.
Answer questions about open issues using your tools; never invent issues or numbers.
${city.neighborhoods.length ? `Known neighborhoods: ${city.neighborhoods.map((n) => n.name).join(', ')}.` : 'Areas are named by the neighborhood or district of each issue.'}
Use query_issues to filter (neighborhood, category, tier, hazard_only) and get_stats for totals.
Use ask_priority_agent or ask_router_agent when the dispatcher asks why an issue is ranked or routed the way it is.
Use ask_route_planner when the dispatcher asks about crew routes, trips, today's schedule or which crew is busiest.
Answer in at most 5 short lines. Cite issues as #<issue_id> with their address and score.`

// Specialist agents run against a copy so a "why?" question never changes stored state.
const quietCtx = (parent) => ({ trace: (e) => parent.trace({ ...e, message: `↳ ${e.agent}: ${e.message}`, agent: 'supervisor' }), delay: false })

function toolSpecs(ctx) {
  return [
    {
      name: 'query_issues',
      description: 'List issues ranked by priority. status: "open" (default), "any", or a specific status.',
      input: z.object({
        neighborhood: z.string().optional(),
        category: z.string().optional(),
        tier: z.enum(['P1', 'P2', 'P3', 'P4']).optional(),
        status: z.string().optional(),
        hazard_only: z.boolean().optional(),
        limit: z.number().int().optional(),
      }),
      fn: tools.queryIssues,
    },
    { name: 'get_stats', description: 'Totals by tier, category, neighborhood and status.', input: z.object({}), fn: tools.getStats },
    { name: 'get_issue', description: 'Full details for one issue.', input: z.object({ issue_id: z.number().int() }), fn: tools.getIssue },
    {
      name: 'ask_priority_agent',
      description: 'Ask the Priority agent to (re)score an issue and explain the factors.',
      input: z.object({ issue_id: z.number().int() }),
      fn: async ({ issue_id }) => {
        const issue = storeGetIssue(issue_id)
        return issue ? runPriority(structuredClone(issue), quietCtx(ctx)) : { error: 'not found' }
      },
    },
    {
      name: 'ask_router_agent',
      description: 'Ask the Router agent which department and crew should take an issue, and why.',
      input: z.object({ issue_id: z.number().int() }),
      fn: async ({ issue_id }) => {
        const issue = storeGetIssue(issue_id)
        return issue ? runRouter(structuredClone(issue), quietCtx(ctx)) : { error: 'not found' }
      },
    },
    {
      name: 'ask_route_planner',
      description: "Ask the Route Planner agent to plan today's crew trips. Returns each crew's trip (jobs, minutes, reason) and deferred jobs. The plan also appears on the Route Plans screen.",
      input: z.object({}),
      fn: async () => {
        const plan = await planRoutes()
        setLastRoutePlan(plan)
        return {
          summary: plan.summary,
          totals: plan.totals,
          trips: plan.trips.map((t) => ({ headline: t.headline, total_min: t.total_min, issue_ids: t.stops.map((s) => s.issue_id), reason: t.reason })),
          deferred: plan.deferred,
        }
      },
    },
  ]
}

// ---------- rule-based fallback ----------

const CATEGORY_WORDS = {
  streets: ['pothole', 'street', 'road', 'sidewalk'],
  traffic_lighting: ['light', 'signal', 'sign'],
  trash: ['trash', 'dumping', 'garbage', 'pickup'],
  water: ['water', 'main', 'flood', 'manhole', 'sewer'],
  property: ['graffiti', 'lot', 'abandoned', 'building'],
  parks_trees: ['tree', 'park', 'limb'],
  animals: ['animal', 'deer', 'dog'],
}

function mockAnswer(question, onTool) {
  const q = question.toLowerCase()
  const neighborhood = city.neighborhoods.find((n) => q.includes(n.name.toLowerCase()))?.name
  const category = Object.entries(CATEGORY_WORDS).find(([, words]) => words.some((w) => q.includes(w)))?.[0]
  if (/how many|stats|total|summary|overview/.test(q)) {
    const s = tools.getStats()
    onTool('get_stats', {}, s)
    const tiers = Object.entries(s.open_by_tier).map(([t, n]) => `${t}: ${n}`).join(', ')
    return `${s.open_issues} open issues from ${s.total_reports} reports (${s.duplicate_reduction_pct}% fewer items after merging duplicates). By tier: ${tiers}.`
  }
  const hazard_only = /danger|hazard|unsafe|safety/.test(q)
  const args = { neighborhood, category, hazard_only, limit: 5 }
  let rows = tools.queryIssues(args)
  onTool('query_issues', args, rows)
  if (!rows.length && hazard_only) {
    rows = tools.queryIssues({ ...args, hazard_only: false })
    onTool('query_issues', { ...args, hazard_only: false }, rows)
  }
  const scope = [neighborhood && `in ${neighborhood}`, category && `(${category.replace('_', ' ')})`].filter(Boolean).join(' ')
  if (!rows.length) return `No open issues ${scope || 'match that question'} right now.`
  const lines = rows.map(
    (r) => `#${r.issue_id} ${r.priority_tier ?? '--'} ${r.priority_score ?? '?'}/100: ${r.summary} at ${r.address.split(',')[0]} (${r.report_count} report${r.report_count === 1 ? '' : 's'}${r.recommended_department ? `, ${r.recommended_department}` : ''})`,
  )
  return `Top ${hazard_only ? 'safety ' : ''}issues${scope ? ` ${scope}` : ''}:\n${lines.join('\n')}`.replace(/ {2,}/g, ' ')
}

export async function askSupervisor(question, ctx) {
  const out = await runStep({
    agent: 'supervisor',
    ctx: { ...ctx, delay: false },
    startMessage: `Question: "${question}"`,
    mock: (onTool) => ({ answer: mockAnswer(question, onTool) }),
    llm: (onTool) =>
      runText({ name: 'supervisor', tier: 'reasoning', systemPrompt: SYSTEM_PROMPT, tools: makeTools(toolSpecs(ctx), onTool), prompt: question }).then(
        ({ text, modelId }) => ({ output: { answer: text.trim() }, modelId }),
      ),
    summarize: (o) => o.answer.split('\n')[0],
  })
  return out.answer
}
