// Intake / Classifier agent (Haiku-class): raw text + location -> structured report.
import { z } from 'zod'
import { cityLabel } from '../lib/data.js'
import * as tools from '../tools/cityTools.js'
import { makeTools, runStructured } from './llm.js'
import { analyzePhotoWithVision } from './photo.js'
import { classifyWithHint, cleanDescription, detectHazards, subcategoryName } from './rules.js'
import { IntakeOutput } from './schemas.js'
import { runStep } from './step.js'

const SYSTEM_PROMPT = `You are the Intake agent for CityCare, a city 311 triage system serving ${cityLabel}.
Residents send short, messy reports (typos, slang, all caps). Your job is to turn one report into a structured record.

Call list_categories first and choose exactly one category and subcategory from it. Use "other"/"unclear" only when the report gives no usable clue.
If photo_analysis is present, a Vision agent has already looked at the resident's photo. Use it: when the text is vague or missing, follow the photo for the category; add hazards the photo shows; if the text and photo disagree, prefer the text unless it says nothing about the problem.
If the report text names streets but no coordinates were given, call geocode_address.
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
]

function mockIntake(report, onTool) {
  const cls = classifyWithHint(report.raw_text, report.category_hint)
  onTool('list_categories', {}, { categories: 8 })
  const photo_analysis = report.photo_url ? tools.analyzePhoto({ photo_url: report.photo_url }) : null
  if (photo_analysis) onTool('analyze_photo', { photo_url: report.photo_url }, photo_analysis)
  const hz = detectHazards(report.raw_text, cls.subcategory, cls.category)
  return {
    category: cls.category,
    subcategory: cls.subcategory,
    description: cleanDescription(report.raw_text),
    hazard_flags: hz.flags,
    hazard_phrases: hz.phrases,
    confidence: cls.confidence,
    photo_analysis,
  }
}

export function runIntake(report, ctx) {
  return runStep({
    agent: 'intake',
    ctx,
    startMessage: `Reading report ${report.report_id}: "${report.raw_text}"`,
    mock: (onTool) => mockIntake(report, onTool),
    llm: async (onTool) => {
      let photo_analysis = null
      if (report.photo_url) {
        photo_analysis = await analyzePhotoWithVision({ photo_url: report.photo_url })
        onTool('analyze_photo', { photo_url: report.photo_url }, photo_analysis)
      }
      const { output, modelId } = await runStructured({
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
          photo_analysis: photo_analysis?.analyzed ? photoBrief(photo_analysis) : null,
          resident_selected_category: report.category_hint || null,
        }),
      })
      // Inherent hazards come from the category table, not the model's judgment.
      return { output: { ...output, hazard_flags: mergeInherent(output), photo_analysis }, modelId }
    },
    summarize: (o) =>
      `Category: ${o.category.replace('_', ' ')} / ${subcategoryName(o.category, o.subcategory)} (confidence ${o.confidence}).` +
      (o.hazard_phrases.length ? ` Hazard words detected: ${o.hazard_phrases.map((p) => `'${p}'`).join(', ')}.` : ' No hazard words.') +
      (o.photo_analysis?.analyzed ? ` Photo: ${o.photo_analysis.shows} (severity ${o.photo_analysis.severity}).` : ''),
  })
}

const photoBrief = ({ shows, is_city_issue, category, subcategory, severity, hazards, confidence }) => ({
  shows,
  is_city_issue,
  category,
  subcategory,
  severity,
  hazards,
  confidence,
})

function mergeInherent(output) {
  const flags = new Set(output.hazard_flags)
  for (const f of detectHazards('', output.subcategory, output.category).flags) flags.add(f)
  return [...flags]
}
