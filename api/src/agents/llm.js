// Thin wrapper around a Strands Agent call: build the agent, stream tool calls into the
// trace, and return validated structured output. Each call gets a fresh Agent so runs
// for different reports never share conversation history.
import { Agent, BedrockModel, Model, ModelThrottledError, tool } from '@strands-agents/sdk'
import { config } from '../config.js'
import { currentStep } from '../lib/callContext.js'
import { createLimiter } from '../lib/limiter.js'

/** Shared by every agent, so bursts of reports, the batch and chat all stay under the quota. */
export const bedrockLimiter = createLimiter({
  maxConcurrent: config.bedrock.maxConcurrent,
  perMinute: config.bedrock.requestsPerMinute,
})

// Backoff schedule for throttles, in seconds (jittered). By default about 2.5 minutes in total
// before a step gives up and falls back to rules; Bedrock's quotas refill per minute.
const THROTTLE_BACKOFF_S = config.bedrock.throttleBackoffS
const isThrottle = (err) =>
  err instanceof ModelThrottledError || /throttl|too many requests|rate exceeded|too many tokens/i.test(`${err?.name} ${err?.message}`)
const jitter = (s) => Math.round(s * 1000 * (0.8 + Math.random() * 0.4))

/** Tell the live trace (if this call belongs to a report step) that we are waiting on Bedrock. */
function noteThrottle(attempt, waitMs, rate) {
  const step = currentStep()
  step?.trace({
    agent: step.agent,
    status: 'tool',
    message: `Bedrock rate limit reached. Waiting ${Math.round(waitMs / 1000)} s before retrying (attempt ${attempt + 1}/${THROTTLE_BACKOFF_S.length}); pacing all model calls at ${rate ?? '∞'}/min.`,
    data: { throttle: true, attempt: attempt + 1, wait_ms: waitMs, per_minute: rate },
  })
}

/**
 * A BedrockModel whose every model call waits for a limiter slot first. If Bedrock still
 * throttles (quota lower than our limits, or shared with other users), the limiter slows
 * every caller down and this call retries with backoff, so a burst slows down instead of
 * dropping to the rule-based fallback.
 */
export class LimitedBedrockModel extends BedrockModel {
  // Strands asks Bedrock's CountTokens API before every model call to size context; that is
  // one more Bedrock request per call, outside our limiter. Our prompts are small, so use the
  // SDK's local estimate instead.
  countTokens(messages, options) {
    return Model.prototype.countTokens.call(this, messages, options)
  }

  async *stream(messages, options) {
    for (let attempt = 0; ; attempt++) {
      const release = await bedrockLimiter.acquire()
      // Hold the stream's opening events until real content arrives, so a throttle that shows
      // up inside the stream (before any content) can still be retried cleanly.
      const held = []
      let flowing = false
      try {
        for await (const event of super.stream(messages, options)) {
          if (!flowing && (event.type === 'modelMessageStartEvent' || event.type === 'modelContentBlockStartEvent')) {
            held.push(event)
            continue
          }
          if (!flowing) {
            flowing = true
            yield* held
          }
          yield event
        }
        if (!flowing) yield* held
        return
      } catch (err) {
        if (flowing || !isThrottle(err)) throw err
        const rate = bedrockLimiter.throttled()
        if (attempt >= THROTTLE_BACKOFF_S.length) {
          throw new ModelThrottledError(
            `Bedrock is still over its rate limit after ${THROTTLE_BACKOFF_S.length} retries (${err.message}). Lower BEDROCK_RPM or request a higher Bedrock quota.`,
            { cause: err },
          )
        }
        const waitMs = jitter(THROTTLE_BACKOFF_S[attempt])
        bedrockLimiter.pause(waitMs)
        noteThrottle(attempt, waitMs, rate)
      } finally {
        release()
      }
    }
  }
}

const models = {}

// Agents are built with retryStrategy: null because LimitedBedrockModel already retries
// throttles with backoff; stacking Strands' own retries would make one step wait many minutes.

/**
 * Model for a tier. maxTokens is the most output a call may produce. Bedrock reserves it
 * against the tokens-per-minute quota when the call starts (newer Claude models count output
 * tokens several times over), so oversized values throttle us without ever being used.
 */
export function modelFor(tier, maxTokens = config.bedrock.maxTokens) {
  const modelId = tier === 'intake' ? config.models.intake : config.models.reasoning
  models[`${modelId}|${maxTokens}`] ??= new LimitedBedrockModel({
    region: config.awsRegion,
    modelId,
    maxTokens,
    // The SDK retries an initial 429 a few times itself before our backoff takes over.
    clientConfig: { maxAttempts: 3, retryMode: 'adaptive' },
  })
  return { model: models[`${modelId}|${maxTokens}`], modelId }
}

/**
 * Wrap plain JS functions as Strands tools. Each spec: { name, description, input (zod), fn }.
 * onCall(name, input, output) is invoked after every call so the pipeline can trace it.
 */
export function makeTools(specs, onCall) {
  return specs.map((s) =>
    tool({
      name: s.name,
      description: s.description,
      inputSchema: s.input,
      callback: async (input) => {
        const output = await s.fn(input)
        onCall?.(s.name, input, output)
        return output
      },
    }),
  )
}

export async function runStructured({ tier, systemPrompt, tools = [], schema, prompt, name, maxTokens }) {
  const { model, modelId } = modelFor(tier, maxTokens)
  const agent = new Agent({ model, name, systemPrompt, tools, structuredOutputSchema: schema, printer: false, retryStrategy: null })
  const result = await agent.invoke(prompt)
  return { output: result.structuredOutput, modelId }
}

export async function runText({ tier, systemPrompt, tools = [], prompt, name, maxTokens = config.bedrock.maxTokensLong }) {
  const { model, modelId } = modelFor(tier, maxTokens)
  const agent = new Agent({ model, name, systemPrompt, tools, printer: false, retryStrategy: null })
  const result = await agent.invoke(prompt)
  return { text: result.toString(), modelId }
}
