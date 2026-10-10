// Dedup agent (Sonnet-class). Code finds candidates by distance, time window and category;
// the LLM decides whether a candidate is the same physical problem.
import { z } from 'zod'
import { cityLabel } from '../lib/data.js'
import { config } from '../config.js'
import * as tools from '../tools/cityTools.js'
import { makeTools, runStructured } from './llm.js'
import { decideDuplicate, dedupRadius } from './rules.js'
import { DedupOutput } from './schemas.js'
import { runStep } from './step.js'

const SYSTEM_PROMPT = `You are the Dedup agent for CityCare, a city 311 triage system serving ${cityLabel}.
You get one new structured report and a short list of candidate open issues that code already found nearby (same category, inside the time window).
Decide whether the report describes the SAME physical problem as one candidate.

Guidance:
- Different wording for the same thing should merge ("streetlight out" vs "dark corner, light broken" 30 m apart).
- Two separate instances of the same kind of problem should NOT merge (two potholes 80 m apart on one block are two issues).
- Spread-out problems (water main breaks, flooding) can be reported from further away than point problems (potholes, signs).
- Use get_issue to read the candidate's existing reports when the description alone is not enough.
- If you are unsure, set duplicate_of to null and put the candidate in possible_duplicate_of so a human reviews it.
Only ever return an issue_id from the candidate list. Finish by calling the structured output tool; do not reply in plain text.`

const toolSpecs = [
  {
    name: 'find_nearby_issues',
    description: 'Open issues within radius_m meters and the last `days` days, optionally of one category.',
    input: z.object({ lat: z.number(), lng: z.number(), radius_m: z.number().optional(), days: z.number().optional(), category: z.string().optional() }),
    fn: tools.findNearbyIssues,
  },
  {
    name: 'semantic_search_issues',
    description: 'Search open issues by text similarity.',
    input: z.object({ text: z.string(), top_k: z.number().int().optional() }),
    fn: tools.semanticSearchIssues,
  },
  {
    name: 'get_issue',
    description: 'Full details of an issue, including the text of every merged report.',
    input: z.object({ issue_id: z.number().int() }),
    fn: tools.getIssue,
  },
]

export function findCandidates(report) {
  return tools.findNearbyIssues({
    lat: report.lat,
    lng: report.lng,
    radius_m: dedupRadius(report.subcategory),
    category: report.category,
    text: report.raw_text,
  })
}

/** Keep the LLM honest: only candidates may be merged into, and only above the confidence threshold. */
function enforce(output, candidates) {
  const ids = new Set(candidates.map((c) => c.issue_id))
  const out = { ...output }
  if (out.duplicate_of != null && !ids.has(out.duplicate_of)) out.duplicate_of = null
  if (out.possible_duplicate_of != null && !ids.has(out.possible_duplicate_of)) out.possible_duplicate_of = null
  if (out.duplicate_of != null && out.confidence < config.dedup.mergeConfidence) {
    out.possible_duplicate_of = out.duplicate_of
    out.duplicate_of = null
    out.reason += ' (Below merge threshold: flagged for review instead of merging.)'
  }
  return out
}

export function runDedup(report, ctx) {
  const candidates = findCandidates(report)
  const radius = dedupRadius(report.subcategory)
  return runStep({
    agent: 'dedup',
    ctx,
    startMessage: `Looking for open ${report.category.replace('_', ' ')} issues within ${radius} m in the last ${config.dedup.windowDays} days: ${candidates.length} candidate${candidates.length === 1 ? '' : 's'}.`,
    mock: (onTool) => {
      onTool('find_nearby_issues', { lat: report.lat, lng: report.lng, radius_m: radius, category: report.category }, candidates)
      return decideDuplicate(report, candidates)
    },
    // No candidates means nothing to judge; skip the LLM call entirely.
    llm: candidates.length
      ? (onTool) =>
          runStructured({
            name: 'dedup',
            tier: 'reasoning',
            systemPrompt: SYSTEM_PROMPT,
            tools: makeTools(toolSpecs, onTool),
            schema: DedupOutput,
            prompt: JSON.stringify({
              new_report: {
                text: report.raw_text,
                category: report.category,
                subcategory: report.subcategory,
                lat: report.lat,
                lng: report.lng,
                address: report.address,
              },
              candidates,
            }),
          }).then(({ output, modelId }) => ({ output: enforce(output, candidates), modelId }))
      : undefined,
    summarize: (o) => (o.duplicate_of ? `${o.reason} Merging.` : o.possible_duplicate_of ? o.reason : `New issue. ${o.reason}`),
  })
}
