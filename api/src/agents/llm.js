// Thin wrapper around a Strands Agent call: build the agent, stream tool calls into the
// trace, and return validated structured output. Each call gets a fresh Agent so runs
// for different reports never share conversation history.
import { Agent, BedrockModel, tool } from '@strands-agents/sdk'
import { config } from '../config.js'

const models = {}

export function modelFor(tier) {
  const modelId = tier === 'intake' ? config.models.intake : config.models.reasoning
  models[modelId] ??= new BedrockModel({ region: config.awsRegion, modelId, maxTokens: 4096 })
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
