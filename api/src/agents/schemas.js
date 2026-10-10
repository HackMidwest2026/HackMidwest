// Structured-output schemas for every agent (Zod). These are the integration contract
// between the agents and the rest of the app: the LLM must return exactly these shapes.
import { z } from 'zod'
import { categories } from '../lib/data.js'

const categoryIds = categories.map((c) => c.id)
const subcategoryIds = categories.flatMap((c) => c.subcategories.map((s) => s.id))

export const IntakeOutput = z.object({
  category: z.enum(categoryIds).describe('Top-level category id from list_categories'),
  subcategory: z.enum(subcategoryIds).describe('Subcategory id belonging to the chosen category'),
  description: z.string().describe('One clean sentence describing the problem, without slang or typos'),
  hazard_flags: z
    .array(z.string())
    .describe('snake_case safety flags, e.g. vehicle_damage_risk, collision_risk, injury_risk, children_present, road_blocked, electrical_hazard'),
  hazard_phrases: z.array(z.string()).describe('Exact phrases from the report that signal danger'),
  confidence: z.number().min(0).max(1),
})

export const DedupOutput = z.object({
  duplicate_of: z.number().int().nullable().describe('issue_id this report should merge into, or null for a new issue'),
  possible_duplicate_of: z
    .number()
    .int()
    .nullable()
    .describe('issue_id that might be the same problem but you are not confident enough to merge; otherwise null'),
  confidence: z.number().min(0).max(1),
  reason: z.string().describe('One or two sentences citing distance, description and timing'),
})

export const PriorityOutput = z.object({
  adjustment: z.number().int().min(-15).max(15).describe('Points to add to the rubric base score, between -15 and +15'),
  reason: z.string().describe('Why the adjustment (or why none) in one or two sentences'),
})

export const RouterOutput = z.object({
  department_id: z.string(),
  crew_id: z.string().nullable(),
  suggested_sla_hours: z.number().int().positive(),
  reason: z.string().describe('Short justification naming workload and distance'),
})
