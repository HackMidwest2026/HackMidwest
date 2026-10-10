// Priority agent (Sonnet-class). Code computes the rubric base score; the LLM may adjust
// it by up to ±15 and must explain why. Keeps scores consistent while allowing judgment.
import { z } from 'zod'
import { reportsForIssue } from '../lib/store.js'
import * as tools from '../tools/cityTools.js'
import { makeTools, runStructured } from './llm.js'
import { baseScore, mockAdjustment, SLA_HOURS, tierFor } from './rules.js'
import { PriorityOutput } from './schemas.js'
import { runStep } from './step.js'

const SYSTEM_PROMPT = `You are the Priority agent for CityOps, Kansas City's 311 triage system.
A deterministic rubric has already scored the issue (safety hazard +40, arterial +15 / collector +8, +3 per extra report up to +15, sensitive site within 200 m +10, +2 per day open up to +10). Critical hazards (signal out, open manhole, main break, tree blocking the road) are raised to a base of at least 80 (P1); lower such an issue only if the report shows the danger is already mitigated.
Your job: adjust the base score by between -15 and +15 points ONLY for things the rubric cannot see, and explain why.
Examples that justify raising: a hazard at night on an unlit arterial, children walking past daily, a hazard that is getting worse, water undermining a road.
Examples that justify lowering: the report describes something cosmetic, or it is already partly mitigated (cone placed, lane closed by police).
photo_findings come from a Vision agent that looked at residents' photos. A photo showing high or critical severity is independent evidence and can justify raising the score; a photo showing only cosmetic damage can justify lowering it.
Most issues need an adjustment of 0. You may call get_issue_history or nearby_sensitive_sites for more context.
Finish by calling the structured output tool; do not reply in plain text.`

const toolSpecs = [
  { name: 'get_road_type', description: 'Road class (arterial/collector/residential) at a point.', input: z.object({ lat: z.number(), lng: z.number() }), fn: tools.getRoadType },
  {
    name: 'nearby_sensitive_sites',
    description: 'Schools, hospitals and senior centers within radius_m (default 200).',
    input: z.object({ lat: z.number(), lng: z.number(), radius_m: z.number().optional() }),
    fn: tools.nearbySensitiveSites,
  },
  { name: 'get_issue_history', description: 'Report count, timing and status history of an issue.', input: z.object({ issue_id: z.number().int() }), fn: tools.getIssueHistory },
]

export function priorityContext(issue, onTool) {
  const point = { lat: issue.lat, lng: issue.lng }
  const road = tools.getRoadType(point)
  onTool?.('get_road_type', point, road)
  const sites = tools.nearbySensitiveSites(point)
  onTool?.('nearby_sensitive_sites', point, sites)
  const days_open = (Date.now() - new Date(issue.first_reported_at).getTime()) / 86400000
  return { road, sites, days_open }
}

function photoFindings(issue) {
  return reportsForIssue(issue.issue_id)
    .filter((r) => r.photo_analysis?.analyzed)
    .map(({ report_id, photo_analysis: p }) => ({ report_id, shows: p.shows, severity: p.severity, hazards: p.hazards }))
}

function finalize(base, adj) {
  const adjustment = Math.max(-15, Math.min(15, Math.round(adj.adjustment)))
  const score = Math.max(0, Math.min(100, base.base_score + adjustment))
  const tier = tierFor(score)
  const factors = [...base.factors]
  if (adjustment) factors.push({ factor: 'agent_adjustment', points: adjustment, detail: adj.reason })
  return {
    base_score: base.base_score,
    adjustment,
    adjustment_reason: adj.reason,
    priority_score: score,
    priority_tier: tier,
    priority_factors: factors,
    response_hours: SLA_HOURS[tier],
  }
}

export function runPriority(issue, ctx) {
  let base
  return runStep({
    agent: 'priority',
    ctx,
    startMessage: `Scoring issue #${issue.issue_id} (${issue.report_count} report${issue.report_count === 1 ? '' : 's'}).`,
    mock: (onTool) => {
      const pctx = priorityContext(issue, onTool)
      base = baseScore(issue, pctx)
      return finalize(base, mockAdjustment(issue, pctx))
    },
    llm: async (onTool) => {
      const pctx = priorityContext(issue, onTool)
      base = baseScore(issue, pctx)
      const { output, modelId } = await runStructured({
        name: 'priority',
        tier: 'reasoning',
        systemPrompt: SYSTEM_PROMPT,
        tools: makeTools(toolSpecs, onTool),
        schema: PriorityOutput,
        prompt: JSON.stringify({
          issue: {
            issue_id: issue.issue_id,
            category: issue.category,
            subcategory: issue.subcategory,
            summary: issue.summary,
            address: issue.address,
            report_count: issue.report_count,
            hazard_flags: issue.hazard_flags,
            lat: issue.lat,
            lng: issue.lng,
          },
          rubric: base,
          context: pctx,
          photo_findings: photoFindings(issue),
        }),
      })
      return { output: finalize(base, output), modelId }
    },
    summarize: (o) => {
      const parts = o.priority_factors.filter((f) => f.points !== 0 && f.factor !== 'agent_adjustment').map((f) => f.detail.toLowerCase())
      const adj = o.adjustment ? ` Agent adjustment ${o.adjustment > 0 ? '+' : ''}${o.adjustment}: ${o.adjustment_reason}` : ''
      return `Score ${o.priority_score}/100 (${o.priority_tier}): ${parts.join(', ') || 'no rubric factors'}.${adj}`
    },
  })
}
