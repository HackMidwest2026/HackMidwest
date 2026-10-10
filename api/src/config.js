import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))

function num(name, fallback) {
  const v = process.env[name]
  return v === undefined || v === '' ? fallback : Number(v)
}

export const config = {
  port: num('PORT', 8080),
  // "mock": deterministic rule-based agents, no AWS needed (default, also the demo fallback).
  // "bedrock": Strands agents backed by Claude on Amazon Bedrock.
  mode: (process.env.CITYOPS_MODE || 'mock').toLowerCase(),
  // Seed JSON (categories, departments, city geography, demo reports).
  dataDir: resolve(process.env.DATA_DIR || join(here, '../../data')),
  // Where runtime state (issues, reports, uploaded photos) is written.
  stateDir: resolve(process.env.STATE_DIR || join(here, '../var')),
  awsRegion: process.env.AWS_REGION || process.env.AWS_DEFAULT_REGION || 'us-east-1',
  // Haiku-class for intake, Sonnet-class for the rest. Some accounts need a cross-region
  // inference profile prefix such as "us." or "global." on these IDs.
  models: {
    intake: process.env.INTAKE_MODEL_ID || 'anthropic.claude-haiku-5-5',
    reasoning: process.env.REASONING_MODEL_ID || 'anthropic.claude-sonnet-5-5',
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
