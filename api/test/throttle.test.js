// Bedrock throttling: adaptive limiter and the retrying model wrapper, with Bedrock simulated.
import assert from 'node:assert/strict'
import { describe, test } from 'node:test'

process.env.CITYCARE_MODE = 'bedrock'
process.env.BEDROCK_THROTTLE_BACKOFF_S = '0.01,0.01,0.01'
process.env.BEDROCK_RPM = '24'
process.env.PHOTON_URL = 'off'

const { BedrockModel, ModelThrottledError } = await import('@strands-agents/sdk')
const { createLimiter } = await import('../src/lib/limiter.js')
const { withStep } = await import('../src/lib/callContext.js')
const { LimitedBedrockModel, bedrockLimiter } = await import('../src/agents/llm.js')

// What Bedrock's ConverseStream returns when the account is over quota (HTTP 429).
const tooMany = () => Object.assign(new Error('Too many requests, please wait before trying again.'), { name: 'ThrottlingException' })
const OK_EVENTS = [
  { type: 'modelMessageStartEvent', role: 'assistant' },
  { type: 'modelContentBlockStartEvent' },
  { type: 'modelContentBlockDeltaEvent', delta: { type: 'textDelta', text: 'hi' } },
  { type: 'modelContentBlockStopEvent' },
  { type: 'modelMessageStopEvent', stopReason: 'endTurn' },
]

/** Replace the real Bedrock call with a script: each entry throws, yields events, or both. */
function scriptBedrock(steps) {
  let call = 0
  BedrockModel.prototype.stream = async function* () {
    const step = steps[Math.min(call++, steps.length - 1)]
    for (const ev of step.before || []) yield ev
    if (step.error) throw step.error()
    for (const ev of step.events || []) yield ev
  }
  return () => call
}

const model = () => new LimitedBedrockModel({ region: 'us-east-2', modelId: 'test-model' })
async function collect(m) {
  const out = []
  for await (const ev of m.stream([], {})) out.push(ev)
  return out
}

describe('adaptive limiter', () => {
  test('a throttle halves the per-minute rate, with a floor', () => {
    const lim = createLimiter({ perMinute: 24, minPerMinute: 2 })
    assert.equal(lim.throttled(), 12)
    assert.equal(lim.throttled(), 12, 'a burst within 2 s counts once')
    assert.equal(lim.stats().throttles, 2)
    assert.equal(lim.stats().current_per_minute, 12)
  })
})

describe('LimitedBedrockModel', () => {
  test('retries "Too many requests" and then succeeds, noting the wait in the trace', async () => {
    const calls = scriptBedrock([{ error: tooMany }, { error: tooMany }, { events: OK_EVENTS }])
    const notes = []
    const events = await withStep({ agent: 'intake', trace: (e) => notes.push(e) }, () => collect(model()))
    assert.equal(calls(), 3)
    assert.deepEqual(events, OK_EVENTS)
    assert.equal(notes.length, 2)
    assert.match(notes[0].message, /Bedrock rate limit reached\. Waiting \d+ s before retrying \(attempt 1\/3\)/)
    assert.ok(bedrockLimiter.stats().throttles >= 2)
  })

  test('a throttle inside the stream, before any content, is retried without duplicate events', async () => {
    const midStream = () => new ModelThrottledError('Too many tokens, please wait before trying again.')
    scriptBedrock([{ before: OK_EVENTS.slice(0, 2), error: midStream }, { events: OK_EVENTS }])
    assert.deepEqual(await collect(model()), OK_EVENTS)
  })

  test('gives up after the backoff schedule with a ModelThrottledError that explains what to do', async () => {
    scriptBedrock([{ error: tooMany }])
    await assert.rejects(collect(model()), (err) => {
      assert.ok(err instanceof ModelThrottledError)
      assert.match(err.message, /still over its rate limit after 3 retries/)
      assert.match(err.message, /BEDROCK_RPM/)
      return true
    })
  })

  test('other errors are not retried', async () => {
    const calls = scriptBedrock([{ error: () => Object.assign(new Error('bad model id'), { name: 'ValidationException' }) }])
    await assert.rejects(collect(model()), /bad model id/)
    assert.equal(calls(), 1)
  })

  test('token counting stays local (no extra Bedrock CountTokens request)', async () => {
    const m = model()
    m._client.send = () => {
      throw new Error('CountTokens should not be called')
    }
    const n = await m.countTokens([{ role: 'user', content: [{ type: 'textBlock', text: 'hello world' }] }])
    assert.ok(Number.isFinite(n) && n > 0)
  })
})
