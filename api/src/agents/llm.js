// Thin wrapper around a Strands Agent call: build the agent, stream tool calls into the
// trace, and return validated structured output. Each call gets a fresh Agent so runs
// for different reports never share conversation history.
import { Agent, BedrockModel, tool } from '@strands-agents/sdk'
import { config } from '../config.js'
import { createLimiter } from '../lib/limiter.js'

/** Shared by every agent, so bursts of reports, the batch and chat all stay under the quota. */
export const bedrockLimiter = createLimiter({
  maxConcurrent: config.bedrock.maxConcurrent,
  perMinute: config.bedrock.requestsPerMinute,
})

const THROTTLE_RETRIES = 3
const isThrottle = (err) => /throttl|too many requests|rate exceeded/i.test(`${err?.name} ${err?.message}`)

/**
 * A BedrockModel whose every model call waits for a limiter slot first. If Bedrock still
 * throttles (the account quota is lower than our limits), all calls pause briefly and this
 * one retries, so a burst slows down instead of dropping to the rule-based fallback.
 */
class LimitedBedrockModel extends BedrockModel {
  async *stream(messages, options) {
    for (let attempt = 0; ; attempt++) {
      const release = await bedrockLimiter.acquire()
      let started = false
      try {
        for await (const event of super.stream(messages, options)) {
          started = true
          yield event
        }
        return
      } catch (err) {
        if (started || attempt >= THROTTLE_RETRIES || !isThrottle(err)) throw err
        bedrockLimiter.pause(5000 * 2 ** attempt)
      } finally {
        release()
      }
    }
  }
}

const models = {}

export function modelFor(tier) {
  const modelId = tier === 'intake' ? config.models.intake : config.models.reasoning
  models[modelId] ??= new LimitedBedrockModel({
    region: config.awsRegion,
    modelId,
    maxTokens: 4096,
    // If a throttle still gets through, back off and retry before the step falls back to rules.
    clientConfig: { maxAttempts: 4, retryMode: 'adaptive' },
  })
  return { model: models[modelId], modelId }
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

export async function runStructured({ tier, systemPrompt, tools = [], schema, prompt, name }) {
  const { model, modelId } = modelFor(tier)
  const agent = new Agent({ model, name, systemPrompt, tools, structuredOutputSchema: schema, printer: false })
  const result = await agent.invoke(prompt)
  return { output: result.structuredOutput, modelId }
}

export async function runText({ tier, systemPrompt, tools = [], prompt, name }) {
  const { model, modelId } = modelFor(tier)
  const agent = new Agent({ model, name, systemPrompt, tools, printer: false })
  const result = await agent.invoke(prompt)
  return { text: result.toString(), modelId }
}
