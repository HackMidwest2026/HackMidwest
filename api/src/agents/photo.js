// Vision agent (Haiku-class, image input). When a report has a photo, the Intake step runs
// this agent first and hands its findings to the Intake agent, so a photo with a vague
// caption ("look at this!!") still gets the right category, hazards and severity.
import { readFile } from 'node:fs/promises'
import { basename, extname, join } from 'node:path'
import { ImageBlock, TextBlock } from '@strands-agents/sdk'
import { config } from '../config.js'
import { runStructured } from './llm.js'
import { PhotoOutput } from './schemas.js'

const FORMATS = { '.png': 'png', '.jpg': 'jpeg', '.jpeg': 'jpeg', '.webp': 'webp', '.gif': 'gif' }

const SYSTEM_PROMPT = `You are the Vision agent for CityCare, Kansas City's 311 triage system.
You look at one photo a resident attached to a report and describe the public-infrastructure problem it shows.
Judge only what is visible. Do not guess at things outside the frame.
Severity: low = cosmetic, medium = needs repair, high = likely to damage a vehicle or injure someone, critical = immediate danger to life (open manhole, downed power line, dark signal at a busy intersection, water main gushing).
If the photo shows no city problem, set is_city_issue to false, severity low, and pick the closest category with low confidence.
Finish by calling the structured output tool; do not reply in plain text.`

/** Runs the vision agent on a photo saved under /uploads. Never throws: failures come back as analyzed: false. */
export async function analyzePhotoWithVision({ photo_url }) {
  const name = basename(String(photo_url || ''))
  const format = FORMATS[extname(name).toLowerCase()]
  if (!String(photo_url).startsWith('/uploads/') || !format) {
    return { analyzed: false, photo_url, note: 'Not an uploaded report photo.' }
  }
  try {
    const bytes = await readFile(join(config.stateDir, 'uploads', name))
    const { output, modelId } = await runStructured({
      name: 'vision',
      tier: 'intake',
      systemPrompt: SYSTEM_PROMPT,
      schema: PhotoOutput,
      prompt: [new TextBlock('Analyze the photo attached to this 311 report.'), new ImageBlock({ format, source: { bytes } })],
    })
    return { analyzed: true, photo_url, model: modelId, ...output }
  } catch (err) {
    return { analyzed: false, photo_url, note: `Photo analysis failed (${err.name}: ${err.message}).` }
  }
}
