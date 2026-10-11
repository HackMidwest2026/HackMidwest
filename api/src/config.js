import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))

function numList(name, fallback) {
  const v = process.env[name]
  return v ? v.split(',').map(Number).filter((n) => Number.isFinite(n) && n >= 0) : fallback
}

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
  // Bedrock mode: keep model calls under the account quota. Extra calls wait in a queue
  // instead of failing with ThrottlingException. One report makes roughly 8-12 calls.
  bedrock: {
    requestsPerMinute: num('BEDROCK_RPM', 24),
    maxConcurrent: num('BEDROCK_MAX_CONCURRENCY', 4),
    // Output-token cap per call. Bedrock reserves it against the tokens-per-minute quota up
    // front, so keep it near what agents actually produce (structured answers are small).
    maxTokens: num('BEDROCK_MAX_TOKENS', 1024),
    // Free-text answers and the route plan.
    maxTokensLong: num('BEDROCK_MAX_TOKENS_LONG', 2048),
    // Seconds to wait before each retry when Bedrock throttles (jittered ±20%).
    throttleBackoffS: numList('BEDROCK_THROTTLE_BACKOFF_S', [8, 15, 30, 45, 60]),
  },
  // SEED_SOURCE=sample loads the bundled sample reports into an empty database (offline demos,
  // tests). Otherwise the app holds only what residents submit on the website.
  seedSample: (process.env.SEED_SOURCE || '').trim().toLowerCase() === 'sample',
  // MongoDB: how often to pull changes made by other API instances sharing the database (0 = off).
  syncIntervalMs: num('SYNC_INTERVAL_MS', 3000),
  // MongoDB: how often to pull other instances' live agent-trace events (0 = off).
  traceSyncMs: num('TRACE_SYNC_MS', 1000),
  // Bedrock mode: reports in the agent pipeline at once; later ones wait their turn.
  reportConcurrency: num('REPORT_CONCURRENCY', 2),
  dedup: {
    radiusM: num('DEDUP_RADIUS_M', 60),
    windowDays: num('DEDUP_WINDOW_DAYS', 14),
    // Below this confidence a match is flagged "possible duplicate" instead of merged.
    mergeConfidence: num('DEDUP_MERGE_CONFIDENCE', 0.6),
  },
}

export const isBedrock = () => config.mode === 'bedrock'
