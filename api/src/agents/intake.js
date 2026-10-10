// Intake / Classifier agent (Haiku-class): raw text + location -> structured report.
import { z } from 'zod'
import { cityLabel } from '../lib/data.js'
import * as tools from '../tools/cityTools.js'
import { makeTools, runStructured } from './llm.js'
import { classifyWithHint, cleanDescription, detectHazards, subcategoryName } from './rules.js'
import { IntakeOutput } from './schemas.js'
import { runStep } from './step.js'

const SYSTEM_PROMPT = `You are the Intake agent for CityCare, a city 311 triage system serving ${cityLabel}.
Residents send short, messy reports (typos, slang, all caps). Your job is to turn one report into a structured record.

Call list_categories first and choose exactly one category and subcategory from it. Use "other"/"unclear" only when the report gives no usable clue.
If the report has a photo, call analyze_photo. If the report text names streets but no coordinates were given, call geocode_address.
Hazard flags are for danger to people or vehicles only (vehicle damage, collisions, injuries, children nearby, blocked road, electrical, flooding). Do not flag mere inconvenience.
If resident_selected_category is set, prefer it unless the text clearly describes a different kind of problem.
Confidence reflects how sure you are of the category: 0.9+ when explicit, about 0.6 when inferred, below 0.4 when guessing.
Finish by calling the structured output tool with your answer; do not reply in plain text.`

const toolSpecs = [
  { name: 'list_categories', description: 'List valid 311 categories and subcategories.', input: z.object({}), fn: tools.listCategories },
  {
    name: 'geocode_address',
    description: 'Geocode a street, intersection or address mentioned in text to lat/lng (local city data, then OpenStreetMap).',
    input: z.object({ text: z.string() }),
    fn: tools.geocodeAddress,
  },
  {
    name: 'reverse_geocode',
    description: 'Get the nearest intersection and neighborhood for coordinates.',
    input: z.object({ lat: z.number(), lng: z.number() }),
    fn: tools.reverseGeocode,
  },
  {
    name: 'analyze_photo',
    description: 'Describe what a report photo shows (pothole, streetlight, dumping...).',
    input: z.object({ photo_url: z.string() }),
    fn: tools.analyzePhoto,
  },
]

function mockIntake(report, onTool) {
  const cls = classifyWithHint(report.raw_text, report.category_hint)
  onTool('list_categories', {}, { categories: 8 })
  if (report.photo_url) onTool('analyze_photo', { photo_url: report.photo_url }, tools.analyzePhoto({ photo_url: report.photo_url }))
  const hz = detectHazards(report.raw_text, cls.subcategory, cls.category)
  return {
    category: cls.category,
    subcategory: cls.subcategory,
    description: cleanDescription(report.raw_text),
    hazard_flags: hz.flags,
    hazard_phrases: hz.phrases,
    confidence: cls.confidence,
  }
}

export function runIntake(report, ctx) {
  return runStep({
    agent: 'intake',
    ctx,
    startMessage: `Reading report ${report.report_id}: "${report.raw_text}"`,
    mock: (onTool) => mockIntake(report, onTool),
    llm: (onTool) =>
      runStructured({
        name: 'intake',
        tier: 'intake',
        systemPrompt: SYSTEM_PROMPT,
        tools: makeTools(toolSpecs, onTool),
        schema: IntakeOutput,
        prompt: JSON.stringify({
          report_text: report.raw_text,
          lat: report.lat,
          lng: report.lng,
          address: report.address,
          photo_url: report.photo_url,
          resident_selected_category: report.category_hint || null,
        }),
      }).then(({ output, modelId }) => ({
        // Inherent hazards come from the category table, not the model's judgment.
        output: { ...output, hazard_flags: mergeInherent(output) },
        modelId,
      })),
    summarize: (o) =>
      `Category: ${o.category.replace('_', ' ')} / ${subcategoryName(o.category, o.subcategory)} (confidence ${o.confidence}).` +
      (o.hazard_phrases.length ? ` Hazard words detected: ${o.hazard_phrases.map((p) => `'${p}'`).join(', ')}.` : ' No hazard words.'),
  })
}

function mergeInherent(output) {
  const flags = new Set(output.hazard_flags)
  for (const f of detectHazards('', output.subcategory, output.category).flags) flags.add(f)
  return [...flags]
}
