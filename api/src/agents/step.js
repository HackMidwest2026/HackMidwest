// Runs one agent step with tracing and graceful degradation:
// Bedrock mode tries the Strands agent and falls back to the rule-based engine on any error,
// so a quota problem or bad model ID never breaks the live demo.
import { config, isBedrock } from '../config.js'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

/**
 * @param {object} p
 * @param {string} p.agent            agent name for the trace
 * @param {object} p.ctx              { trace(evt), delay?: boolean, forceMock?: boolean }
 * @param {string} p.startMessage
 * @param {() => object} p.mock       rule-based implementation (sync)
 * @param {(onTool) => Promise<{output, modelId}>} [p.llm]  Strands implementation
 * @param {(output) => string} p.summarize   one-line message for the completed event
 */
export async function runStep({ agent, ctx, startMessage, mock, llm, summarize }) {
  const started = Date.now()
  ctx.trace({ agent, status: 'started', message: startMessage })
  const onTool = (name, input, output) =>
    ctx.trace({ agent, status: 'tool', message: `${name}(${brief(input)})`, data: { tool: name, input, output } })

  let output
  let engine = 'mock'
  let model
  if (isBedrock() && llm && !ctx.forceMock) {
    try {
      const r = await llm(onTool)
      output = r.output
      model = r.modelId
      engine = 'bedrock'
    } catch (err) {
      ctx.trace({ agent, status: 'error', message: `LLM call failed (${err.name}: ${err.message}). Falling back to rules.` })
      engine = 'fallback'
    }
  }
  if (output === undefined) {
    output = mock(onTool)
    if (ctx.delay !== false && config.mockDelayMs > 0) await sleep(config.mockDelayMs)
  }
  ctx.trace({
    agent,
    status: 'completed',
    message: summarize(output),
    data: output,
    engine,
    ...(model && { model }),
    duration_ms: Date.now() - started,
  })
  return output
}

function brief(input) {
  return Object.entries(input || {})
    .map(([k, v]) => `${k}=${typeof v === 'string' ? JSON.stringify(v.length > 40 ? v.slice(0, 40) + '…' : v) : JSON.stringify(v)}`)
    .join(', ')
}
