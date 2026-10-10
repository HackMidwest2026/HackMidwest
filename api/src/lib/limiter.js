// FIFO limiter: at most `maxConcurrent` holders at once and at most `perMinute` acquisitions
// in any rolling 60 s window. Callers past either limit wait their turn instead of failing.
// Used to keep Bedrock calls under the account quota and to queue reports in Bedrock mode.
//
// The per-minute rate is adaptive (AIMD, like TCP congestion control): each throttle from the
// upstream service halves the current rate, and quiet periods add it back one step at a time
// up to the configured ceiling. That keeps us under the real quota even when we can't know it
// exactly: the token-per-minute quota runs out first, or teammates share the AWS account.

const WINDOW_MS = 60_000
const RECOVER_EVERY_MS = 20_000 // after this long without a throttle, allow one more call/min

export function createLimiter({ maxConcurrent = Infinity, perMinute = Infinity, minPerMinute = 2 } = {}) {
  const waiting = []
  const starts = []
  let active = 0
  let timer = null
  let pausedUntil = 0
  let rate = perMinute
  let lastThrottle = 0
  let lastStep = 0
  let throttles = 0

  function wakeAt(ms) {
    if (timer) return
    timer = setTimeout(() => {
      timer = null
      pump()
    }, ms)
  }

  function recover(now) {
    if (!Number.isFinite(perMinute) || rate >= perMinute) return
    const since = Math.max(lastThrottle, lastStep)
    if (now - since >= RECOVER_EVERY_MS) {
      rate = Math.min(perMinute, rate + 1)
      lastStep = now
    }
  }

  function pump() {
    const now = Date.now()
    // Paused after the upstream service pushed back: hand out nothing until the pause ends.
    if (now < pausedUntil) return waiting.length && wakeAt(pausedUntil - now + 10)
    recover(now)
    while (starts.length && now - starts[0] >= WINDOW_MS) starts.shift()
    while (waiting.length && active < maxConcurrent && starts.length < rate) {
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
    if (waiting.length && starts.length >= rate) wakeAt(WINDOW_MS - (now - starts[0]) + 10)
  }

  const currentRate = () => (Number.isFinite(rate) ? rate : null)

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
    /** The upstream service throttled us: halve the per-minute rate (not below minPerMinute). */
    throttled: () => {
      const now = Date.now()
      throttles++
      // Several in-flight calls often fail together; count one burst as one throttle.
      if (now - lastThrottle > 2000 && Number.isFinite(rate)) rate = Math.max(minPerMinute, Math.floor(rate / 2))
      lastThrottle = now
      return currentRate()
    },
    /** True when a new acquire() would have to wait. */
    isBusy: () =>
      waiting.length > 0 ||
      active >= maxConcurrent ||
      Date.now() < pausedUntil ||
      starts.filter((t) => Date.now() - t < WINDOW_MS).length >= rate,
    stats: () => ({
      active,
      waiting: waiting.length,
      last_minute: starts.filter((t) => Date.now() - t < WINDOW_MS).length,
      max_concurrent: Number.isFinite(maxConcurrent) ? maxConcurrent : null,
      per_minute: Number.isFinite(perMinute) ? perMinute : null,
      current_per_minute: currentRate(),
      throttles,
      paused_ms: Math.max(0, pausedUntil - Date.now()),
    }),
  }
}
