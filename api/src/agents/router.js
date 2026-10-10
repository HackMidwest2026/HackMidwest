// Router / Dispatch agent (Sonnet-class): prioritized issue -> department, crew, SLA, reason.
import { z } from 'zod'
import { departments } from '../lib/data.js'
import * as tools from '../tools/cityTools.js'
import { makeTools, runStructured } from './llm.js'
import { departmentName, pickCrew, SLA_HOURS } from './rules.js'
import { RouterOutput } from './schemas.js'
import { runStep } from './step.js'

const SYSTEM_PROMPT = `You are the Router agent for CityOps, Kansas City's 311 triage system.
Recommend which department and crew should handle a prioritized issue. A human dispatcher approves your recommendation.
Call list_departments, then get_crew_workload and get_crew_locations for the matching department.
Pick the crew with the best balance of distance and spare capacity; never pick a crew at or over capacity if another has room.
Issues in category "other" go to department "human_review".
suggested_sla_hours must follow the tier: P1 24, P2 72, P3 168, P4 336.
The reason should be one short sentence naming the crew's open jobs and distance.
Finish by calling the structured output tool; do not reply in plain text.`

const toolSpecs = [
  { name: 'list_departments', description: 'City departments and the categories each handles.', input: z.object({}), fn: tools.listDepartments },
  {
    name: 'get_crew_workload',
    description: 'Open jobs and capacity for each crew in a department.',
    input: z.object({ department_id: z.string() }),
    fn: tools.getCrewWorkload,
  },
  {
    name: 'get_crew_locations',
    description: 'Crew home bases and distance (km) from a point.',
    input: z.object({ department_id: z.string(), lat: z.number(), lng: z.number() }),
    fn: tools.getCrewLocations,
  },
]

function crewsWithDistance(issue, departmentId) {
  const locs = tools.getCrewLocations({ department_id: departmentId, lat: issue.lat, lng: issue.lng })
  const load = tools.getCrewWorkload({ department_id: departmentId })
  return locs.map((l) => ({ ...l, ...load.find((w) => w.crew_id === l.crew_id) }))
}

function validate(output, issue) {
  const dept = departments.find((d) => d.department_id === output.department_id)
  if (!dept) throw new Error(`Unknown department ${output.department_id}`)
  const crew = output.crew_id ? tools.getCrewWorkload({ department_id: dept.department_id }).find((c) => c.crew_id === output.crew_id) : null
  return {
    ...output,
    crew_id: crew ? crew.crew_id : null,
    suggested_sla_hours: SLA_HOURS[issue.priority_tier] ?? output.suggested_sla_hours,
  }
}

export function runRouter(issue, ctx) {
  return runStep({
    agent: 'router',
    ctx,
    startMessage: `Finding a department and crew for issue #${issue.issue_id} (${issue.priority_tier}).`,
    mock: (onTool) => {
      const deptId = tools.listDepartments().find((d) => d.categories_handled.includes(issue.category))?.department_id ?? 'human_review'
      const crews = crewsWithDistance(issue, deptId)
      onTool('get_crew_workload', { department_id: deptId }, crews.map(({ crew_id, open_jobs, capacity }) => ({ crew_id, open_jobs, capacity })))
      return pickCrew(issue, crews)
    },
    llm: (onTool) =>
      runStructured({
        name: 'router',
        tier: 'reasoning',
        systemPrompt: SYSTEM_PROMPT,
        tools: makeTools(toolSpecs, onTool),
        schema: RouterOutput,
        prompt: JSON.stringify({
          issue_id: issue.issue_id,
          category: issue.category,
          subcategory: issue.subcategory,
          summary: issue.summary,
          priority_tier: issue.priority_tier,
          priority_score: issue.priority_score,
          lat: issue.lat,
          lng: issue.lng,
        }),
      }).then(({ output, modelId }) => ({ output: validate(output, issue), modelId })),
    summarize: (o) => `Recommend ${departmentName(o.department_id)}. ${o.reason} SLA ${o.suggested_sla_hours} h.`,
  })
}
