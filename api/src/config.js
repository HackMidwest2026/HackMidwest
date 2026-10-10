import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))

function num(name, fallback) {
  const v = process.env[name]
  return v === undefined || v === '' ? fallback : Number(v)
}

// CITYCARE_MODE is the current name; CITYOPS_MODE is accepted from before the rename.
// Values are trimmed and unquoted so `bedrock `, "bedrock" or a CRLF .env still work.
function readMode() {
  for (const name of ['CITYCARE_MODE', 'CITYOPS_MODE']) {
    const raw = (process.env[name] || '').trim().replace(/^['"]|['"]$/g, '').toLowerCase()
    if (raw) return { mode: raw, source: name }
  }
  return { mode: 'mock', source: 'default' }
}
const modeInfo = readMode()

export const config = {
  port: num('PORT', 8080),
  // "mock": deterministic rule-based agents, no AWS needed (default, also the demo fallback).
  // "bedrock": Strands agents backed by Claude on Amazon Bedrock.
  mode: modeInfo.mode,
  modeSource: modeInfo.source,
  // Seed JSON (categories, departments, city geography, demo reports).
  dataDir: resolve(process.env.DATA_DIR || join(here, '../../data')),
  // Where runtime state (issues, reports, uploaded photos) is written.
  stateDir: resolve(process.env.STATE_DIR || join(here, '../var')),
  awsRegion: process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'us-east-2',
  // Haiku-class for intake, Sonnet-class for the rest. Defaults are the cross-region
  // inference profiles verified on the team's account in us-east-2.
  models: {
    intake: process.env.INTAKE_MODEL_ID || 'us.anthropic.claude-haiku-4-5-20251001-v1:0',
    reasoning: process.env.REASONING_MODEL_ID || 'us.anthropic.claude-sonnet-4-6',
  },
  // Artificial per-agent delay in mock mode so the live trace is watchable in a demo.
  mockDelayMs: num('MOCK_DELAY_MS', 350),
  // Per-report pacing for the demo batch in mock mode (50 reports x 80 ms = about 4 s).
  mockBatchDelayMs: num('MOCK_BATCH_DELAY_MS', 80),
  dedup: {
    radiusM: num('DEDUP_RADIUS_M', 60),
    windowDays: num('DEDUP_WINDOW_DAYS', 14),
    // Below this confidence a match is flagged "possible duplicate" instead of merged.
    mergeConfidence: num('DEDUP_MERGE_CONFIDENCE', 0.6),
  },
}

export const isBedrock = () => config.mode === 'bedrock'
