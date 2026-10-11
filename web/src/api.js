// Tiny API client. All paths are relative so the same build works behind Vite's dev
// proxy and behind nginx in Docker.
async function request(method, path, body) {
  const res = await fetch(path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || `${res.status} ${res.statusText}`)
  return data
}

const qs = (o) => new URLSearchParams(Object.entries(o).filter(([, v]) => v != null && v !== '')).toString()

export const api = {
  meta: () => request('GET', '/api/meta'),
  issues: (status = 'all') => request('GET', `/api/issues?status=${status}`),
  issue: (id) => request('GET', `/api/issues/${id}`),
  stats: () => request('GET', '/api/stats'),
  crews: () => request('GET', '/api/crews'),
  nearby: (lat, lng, text) => request('GET', `/api/nearby?${qs({ lat, lng, text, radius: 120 })}`),
  submitReport: (body) => request('POST', '/api/reports', body),
  approve: (id, body) => request('POST', `/api/issues/${id}/approve`, body),
  reject: (id, reason) => request('POST', `/api/issues/${id}/reject`, { reason }),
  setStatus: (id, status) => request('PATCH', `/api/issues/${id}`, { status }),
  addressSuggest: (q, near) => request('GET', `/api/address-suggest?${qs({ q, lat: near?.lat, lng: near?.lng })}`),
  geocode: (q, near) => request('GET', `/api/geocode?${qs({ q, lat: near?.lat, lng: near?.lng })}`),
  reverseGeocode: (lat, lng) => request('GET', `/api/reverse-geocode?lat=${lat}&lng=${lng}`),
  chat: (question) => request('POST', '/api/chat', { question }),
  runDemoBatch: () => request('POST', '/api/demo/batch', {}),
  resetDemo: () => request('POST', '/api/demo/reset', {}),
  routes: () => request('GET', '/api/routes'),
  planRoutes: () => request('POST', '/api/routes/plan', {}),
}

/** Subscribe to the live trace/issue stream. Returns an unsubscribe function. */
export function subscribe({ onTrace, onIssue, onStatus, onReload }) {
  const es = new EventSource('/api/stream')
  es.addEventListener('hello', () => onStatus?.('live'))
  es.addEventListener('trace', (e) => onTrace?.(JSON.parse(e.data)))
  es.addEventListener('issue', (e) => onIssue?.(JSON.parse(e.data)))
  es.addEventListener('reload', () => onReload?.())
  es.onerror = () => onStatus?.('reconnecting')
  return () => es.close()
}

export function newRunId() {
  return globalThis.crypto?.randomUUID ? crypto.randomUUID() : `run-${Date.now()}-${Math.random().toString(16).slice(2)}`
}
