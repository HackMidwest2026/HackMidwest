// Carries the current agent step's trace function down to the model layer (through Strands'
// async generators), so a Bedrock throttle can show up in that report's live trace.
import { AsyncLocalStorage } from 'node:async_hooks'

const storage = new AsyncLocalStorage()

/** Run `fn` with `{ agent, trace }` available to currentStep() anywhere below it. */
export const withStep = (step, fn) => storage.run(step, fn)

export const currentStep = () => storage.getStore()
