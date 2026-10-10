// FIFO limiter: at most `maxConcurrent` holders at once and at most `perMinute` acquisitions
// in any rolling 60 s window. Callers past either limit wait their turn instead of failing.
// Used to keep Bedrock calls under the account quota and to queue reports in Bedrock mode.

const WINDOW_MS = 60_000

export function createLimiter({ maxConcurrent = Infinity, perMinute = Infinity } = {}) {
  const waiting = []
  const starts = []
  let active = 0
  let timer = null
  let pausedUntil = 0

  function wakeAt(ms) {
    if (timer) return
    timer = setTimeout(() => {
      timer = null
      pump()
    }, ms)
  }

  function pump() {
    const now = Date.now()
    // Paused after the upstream service pushed back: hand out nothing until the pause ends.
    if (now < pausedUntil) return waiting.length && wakeAt(pausedUntil - now + 10)
    while (starts.length && now - starts[0] >= WINDOW_MS) starts.shift()
    while (waiting.length && active < maxConcurrent && starts.length < perMinute) {
      active++
      starts.push(now)
      let released = false
      waiting.shift()(() => {
        if (released) return
        released = true
        active--
        pump()
      })
    }
    // Rate-limited (not concurrency-limited): wake up when the oldest call leaves the window.
    if (waiting.length && starts.length >= perMinute) wakeAt(WINDOW_MS - (now - starts[0]) + 10)
  }

  return {
    /** Resolves with a release() function once a slot is free. Always call release(). */
    acquire: () =>
      new Promise((resolve) => {
        waiting.push(resolve)
        pump()
      }),
    /** Stop handing out slots for `ms` (callers keep their place in line). */
    pause: (ms) => {
      pausedUntil = Math.max(pausedUntil, Date.now() + ms)
    },
    /** True when a new acquire() would have to wait. */
    isBusy: () =>
      waiting.length > 0 ||
      active >= maxConcurrent ||
      Date.now() < pausedUntil ||
      starts.filter((t) => Date.now() - t < WINDOW_MS).length >= perMinute,
    stats: () => ({
      active,
      waiting: waiting.length,
      last_minute: starts.filter((t) => Date.now() - t < WINDOW_MS).length,
      max_concurrent: Number.isFinite(maxConcurrent) ? maxConcurrent : null,
      per_minute: Number.isFinite(perMinute) ? perMinute : null,
      paused_ms: Math.max(0, pausedUntil - Date.now()),
    }),
  }
}
